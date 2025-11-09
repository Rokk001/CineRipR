"""Archive extraction and 7-Zip handling."""

from __future__ import annotations

import logging
import os
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

from .archive_constants import UNWANTED_EXTRACTED_SUFFIXES
from .progress import ProgressTracker


def fix_file_permissions(directory: Path) -> None:
    """Fix file permissions for extracted files to be readable/writable by owner and group.

    This is particularly important when running in Docker containers where files
    might be created with restrictive permissions.

    Args:
        directory: Directory containing extracted files to fix permissions for
    """
    try:
        for root, dirs, files in os.walk(directory):
            # Fix directory permissions (755: rwxr-xr-x)
            for d in dirs:
                dir_path = Path(root) / d
                try:
                    dir_path.chmod(
                        stat.S_IRWXU
                        | stat.S_IRGRP
                        | stat.S_IXGRP
                        | stat.S_IROTH
                        | stat.S_IXOTH
                    )
                except OSError:
                    pass

            # Fix file permissions (644: rw-r--r--)
            for f in files:
                file_path = Path(root) / f
                try:
                    file_path.chmod(
                        stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
                    )
                except OSError:
                    pass
    except OSError:
        pass


def detect_archive_format(archive: Path) -> str | None:
    """Detect the archive format by file extension.

    Returns:
        Format name (e.g., 'rar', 'zip', 'tar', 'dctmp') or None if unknown
    """
    lower = archive.name.lower()
    if lower.endswith(".rar"):
        return "rar"
    if lower.endswith(".dctmp"):
        return "dctmp"
    for format_name, suffixes, _description in shutil.get_unpack_formats():
        for suffix in suffixes:
            if lower.endswith(suffix.lower()):
                return format_name
    return None


def resolve_seven_zip_command(seven_zip_path: Path | None) -> str | None:
    """Find 7-Zip executable path.

    Args:
        seven_zip_path: User-configured path or None for auto-detection

    Returns:
        Path to 7-Zip executable or None if not found
    """
    if seven_zip_path is not None:
        candidate = Path(seven_zip_path)
        if candidate.is_absolute():
            return str(candidate)
        resolved = shutil.which(str(candidate))
        if resolved:
            return resolved
        candidate = (Path.cwd() / candidate).resolve()
        if candidate.exists():
            return str(candidate)
        return str(seven_zip_path)

    # Auto-detect common 7-Zip executables
    for name in ("7z", "7za", "7zr"):
        resolved = shutil.which(name)
        if resolved:
            return resolved
    return None


def get_rar_volume_count(
    archive: Path, *, seven_zip_path: Path | None
) -> tuple[int | None, str | None]:
    """Get the total number of volumes for a RAR archive from its header.

    Args:
        archive: RAR archive file to check
        seven_zip_path: Path to 7-Zip executable

    Returns:
        Tuple of (volume_count, error_message)
        - volume_count: Number of volumes if successfully read, None otherwise
        - error_message: Error description if failed, None if successful
    """
    command = resolve_seven_zip_command(seven_zip_path)
    if command is None:
        return None, "7-Zip executable not found"

    try:
        # Use 7-Zip 'l' command to list archive information
        result = subprocess.run(
            [command, "l", str(archive)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )

        if result.returncode != 0:
            return None, f"7-Zip list failed (exit code {result.returncode})"

        # Parse output for volume count
        # Look for "Volumes: 92" or "Volumes: 1" in the output
        output = result.stdout + result.stderr
        volume_match = re.search(r"Volumes:\s*(\d+)", output, re.IGNORECASE)
        if volume_match:
            return int(volume_match.group(1)), None

        # If no volume count found, assume single volume
        return 1, None

    except subprocess.TimeoutExpired:
        return None, "7-Zip list command timed out"
    except Exception as exc:
        return None, f"Failed to read RAR volume count: {exc}"


def can_extract_archive(
    archive: Path, *, seven_zip_path: Path | None
) -> tuple[bool, str | None]:
    """Check if an archive can be extracted and validate its integrity.

    Returns:
        Tuple of (can_extract, error_message)
    """
    format_name = detect_archive_format(archive)

    if format_name == "rar":
        command = resolve_seven_zip_command(seven_zip_path)
        if command is None:
            return (
                False,
                "7-Zip executable not found. Configure [tools].seven_zip or install 7-Zip.",
            )
        return True, None

    if format_name == "dctmp":
        # DCTMP files are temporary archive files that should be handled by 7-Zip
        command = resolve_seven_zip_command(seven_zip_path)
        if command is None:
            return (
                False,
                "7-Zip executable not found. Configure [tools].seven_zip or install 7-Zip.",
            )
        return True, None

    if format_name == "zip":
        try:
            with zipfile.ZipFile(archive) as zf:
                damaged = zf.testzip()
                if damaged is not None:
                    return False, f"corrupt member: {damaged}"
        except (OSError, zipfile.BadZipFile) as exc:
            return False, str(exc)
        return True, None

    if format_name in {"tar", "gztar", "bztar", "xztar"}:
        try:
            with tarfile.open(archive) as tf:
                for _member in tf:
                    pass
        except (OSError, tarfile.TarError) as exc:
            return False, str(exc)
        return True, None

    return True, None


def _win_long_path(p: Path) -> str:
    """Convert path to Windows long path format (\\\\?\\) for paths > 260 chars."""
    text = str(p)
    if os.name != "nt":
        return text

    # Normalize to absolute path
    try:
        p = p.resolve()
    except OSError:
        pass

    s = str(p)
    if s.startswith("\\\\?\\"):
        return s
    if s.startswith("\\\\"):
        # UNC path => \\?\UNC\server\share\...
        return "\\\\?\\UNC" + s[1:]
    return "\\\\?\\" + s


def _extract_with_seven_zip(
    command: str,
    archive: Path,
    target_dir: Path,
    *,
    cpu_cores: int = 2,
    progress: ProgressTracker | None = None,
    logger: logging.Logger | None = None,
    part_count: int = 1,
) -> None:
    """Extract RAR archive using 7-Zip with progress tracking.

    Args:
        command: Path to 7-Zip executable
        archive: Archive file to extract
        target_dir: Target directory for extraction
        cpu_cores: Number of CPU cores to use for extraction (default: 2)
        progress: Optional progress tracker
        logger: Optional logger for progress updates
    """
    target_dir.mkdir(parents=True, exist_ok=True)

    # Build 7-Zip command with Windows long path support
    output_arg = f"-o{_win_long_path(target_dir)}"
    archive_arg = _win_long_path(archive)
    mmt_arg = f"-mmt{cpu_cores}"  # Set number of CPU threads

    process = subprocess.Popen(
        [
            command,
            "x",  # Extract with full paths
            archive_arg,
            output_arg,
            "-y",  # Yes to all prompts
            mmt_arg,  # Number of CPU threads
            "-bsp1",  # Show progress percentage
            "-bso1",  # Stdout messages
            "-bb1",  # Basic output
            "-x!*.sfv",  # Exclude .sfv files
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    # Parse progress from stdout and update using ProgressTracker
    if process.stdout is None:
        stdout_lines: list[str] = []
    else:
        stdout_lines = []
        last_percent = -1
        progress_shown = False
        
        # Show initial progress message
        if progress is not None and logger is not None:
            progress.log(logger, f"Extracting {archive.name}...")
        
        for line in process.stdout:
            stdout_lines.append(line)
            text = line.strip()
            
            # Log 7-Zip output for debugging
            if logger and text:
                logger.debug(f"7-Zip output: {text}")
            
            # Parse percentage from 7z output (e.g., " 12%")
            m = re.search(r"(\d{1,3})%", text)
            if m:
                percent = max(0, min(100, int(m.group(1))))
                progress_shown = True

                # Update progress tracker when percent changes
                if (
                    percent != last_percent
                    and progress is not None
                    and logger is not None
                ):
                    last_percent = percent

                    # Calculate current part being processed based on percent
                    # At 99% with 66 parts, we want to show 65/66 (not 64/66)
                    current_part = max(1, int(round((percent / 100) * part_count)))
                    # Cap at part_count
                    current_part = min(current_part, part_count)

                    message = f"Extracting {archive.name}"
                    progress.advance(logger, message, absolute=current_part)
        
        # If no progress was shown, show completion message
        if not progress_shown and progress is not None and logger is not None:
            progress.complete(logger, f"Extracted {archive.name}")

    process.wait()

    # Complete the progress tracker (only if not already completed)
    if process.returncode == 0 and progress is not None and logger is not None:
        # Only complete if we haven't already shown completion
        if progress.current < progress.total:
            message = f"Extracting {archive.name}"
            progress.complete(logger, message)
        # Fix permissions after successful extraction
        fix_file_permissions(target_dir)

    # Handle extraction failure with temp directory fallback
    if process.returncode != 0:
        stderr = "".join(stdout_lines).strip()

        # Fallback: extract to temporary short path, then move to target
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_out = Path(tmpdir)
                tmp_arg = f"-o{str(tmp_out)}"
                retry = subprocess.run(
                    [
                        command,
                        "x",
                        archive_arg,
                        tmp_arg,
                        "-y",
                        mmt_arg,  # Use same CPU cores for fallback
                        "-bsp1",
                        "-bso1",
                        "-bb1",
                        "-x!*.sfv",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if retry.returncode == 0:
                    # Move contents from tmp to target
                    target_dir.mkdir(parents=True, exist_ok=True)

                    # Remove unwanted files before moving
                    for unwanted in UNWANTED_EXTRACTED_SUFFIXES:
                        try:
                            for p in tmp_out.rglob(f"*{unwanted}"):
                                try:
                                    p.unlink()
                                except OSError:
                                    pass
                        except OSError:
                            pass

                    # Move all files from temp to target
                    for item in tmp_out.iterdir():
                        dest = target_dir / item.name
                        try:
                            shutil.move(str(item), str(dest))
                        except OSError:
                            pass
                    # Fix permissions after successful extraction
                    fix_file_permissions(target_dir)
                    return
        except Exception:
            pass

        raise RuntimeError(
            f"7-Zip extraction failed (exit code {process.returncode})"
            + (f": {stderr}" if stderr else "")
        )


def extract_archive(
    archive: Path,
    target_dir: Path,
    *,
    seven_zip_path: Path | None,
    cpu_cores: int = 2,
    progress: ProgressTracker | None = None,
    logger: logging.Logger | None = None,
    part_count: int = 1,
) -> None:
    """Extract an archive to the target directory.

    Args:
        archive: Archive file to extract
        target_dir: Target directory for extraction
        seven_zip_path: Path to 7-Zip executable (for RAR files)
        cpu_cores: Number of CPU cores to use for extraction (default: 2)
        progress: Optional progress tracker
        logger: Optional logger for progress updates

    Raises:
        RuntimeError: If extraction fails
    """
    format_name = detect_archive_format(archive)

    if format_name == "rar":
        command = resolve_seven_zip_command(seven_zip_path)
        if command is None:
            raise RuntimeError(
                "7-Zip executable not found. Configure [tools].seven_zip or install 7-Zip."
            )
        _extract_with_seven_zip(
            command,
            archive,
            target_dir,
            cpu_cores=cpu_cores,
            progress=progress,
            logger=logger,
            part_count=part_count,
        )
    elif format_name == "dctmp":
        # DCTMP files are temporary archive files that should be handled by 7-Zip
        command = resolve_seven_zip_command(seven_zip_path)
        if command is None:
            raise RuntimeError(
                "7-Zip executable not found. Configure [tools].seven_zip or install 7-Zip."
            )
        _extract_with_seven_zip(
            command,
            archive,
            target_dir,
            cpu_cores=cpu_cores,
            progress=progress,
            logger=logger,
            part_count=part_count,
        )
    else:
        # Use shutil for other formats
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.unpack_archive(str(archive), str(target_dir))
        if progress is not None and logger is not None:
            logger.info("Extracted %s", archive.name)

    # Fix file permissions after extraction (important for Docker environments)
    fix_file_permissions(target_dir)


__all__ = [
    "detect_archive_format",
    "resolve_seven_zip_command",
    "get_rar_volume_count",
    "can_extract_archive",
    "extract_archive",
    "fix_file_permissions",
]
