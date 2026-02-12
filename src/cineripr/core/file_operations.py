"""File and directory operations for archive processing."""

from __future__ import annotations

import logging
import os
import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

from ..extraction.archive_detection import is_supported_archive
from ..progress import ProgressTracker

if TYPE_CHECKING:
    from ..web.settings_db import SettingsDB



def _is_unc_path(path: Path) -> bool:
    """Check if path is a Windows UNC path.

    Args:
        path: Path to check

    Returns:
        True if path is a UNC path, False otherwise
    """
    path_str = str(path)
    return path_str.startswith("\\\\") or path_str.startswith("//")


def _normalize_path_for_docker(path: Path) -> Path:
    """Normalize path for Docker container compatibility.

    Args:
        path: Path to normalize

    Returns:
        Normalized path
    """
    path_str = str(path)

    # Handle Windows UNC paths in Docker
    if _is_unc_path(path):
        # Convert UNC path to Docker mount path
        # \\SERVER\Share\path -> /data/downloads/path
        if path_str.startswith("\\\\"):
            # Remove \\ and convert to Unix-style path
            path_str = path_str[2:]
            # Replace backslashes with forward slashes
            path_str = path_str.replace("\\", "/")
            # Add /data prefix for Docker mount
            if not path_str.startswith("/data/"):
                path_str = "/data/" + path_str

    return Path(path_str)


def _safe_move_with_retry(src: Path, dst: Path, logger: logging.Logger = None) -> bool:
    """Safely move files with multiple retry strategies for Docker/UNC paths.

    Args:
        src: Source file path
        dst: Destination file path
        logger: Optional logger for error messages

    Returns:
        True if move was successful, False otherwise
    """
    # Ensure destination directory exists
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Strategy 1: Direct move
    try:
        shutil.move(str(src), str(dst))
        return True
    except OSError as e:
        if logger:
            logger.warning("Direct move failed for %s: %s", src.name, e)

    # Strategy 2: Copy + delete (for read-only filesystems)
    try:
        shutil.copy2(str(src), str(dst))


        # Try to delete original
        try:
            src.unlink()
        except OSError as delete_error:
            if logger:
                logger.warning(
                    "Could not delete original file %s: %s", src, delete_error
                )

        return True
    except OSError as e:
        if logger:
            logger.error("Copy fallback also failed for %s: %s", src.name, e)

    # Strategy 3: Try with normalized paths (for UNC paths in Docker)
    if _is_unc_path(src):
        try:
            normalized_src = _normalize_path_for_docker(src)
            normalized_dst = _normalize_path_for_docker(dst)

            if logger:
                logger.info(
                    "Trying normalized paths: %s -> %s", normalized_src, normalized_dst
                )

            # Ensure normalized destination directory exists
            normalized_dst.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(normalized_src), str(normalized_dst))

            return True
        except OSError as e:
            if logger:
                logger.error("Normalized path move also failed for %s: %s", src.name, e)

    return False


def ensure_unique_destination(destination: Path) -> Path:
    """Return the destination path, allowing overwrites.

    Args:
        destination: Desired destination path

    Returns:
        Destination path (existing files will be overwritten)
    """
    return destination


def cleanup_failed_extraction_dir(target_dir: Path, *, pre_existing: bool) -> None:
    """Remove empty extraction directory if it was created by this extraction attempt.

    Args:
        target_dir: Directory that was created for extraction
        pre_existing: Whether the directory existed before extraction
    """
    if pre_existing:
        return

    try:
        if (
            target_dir.exists()
            and target_dir.is_dir()
            and not any(target_dir.iterdir())
        ):
            target_dir.rmdir()
    except OSError:
        pass


def handle_extraction_failure(
    logger: logging.Logger,
    target_dir: Path,
    extracted_targets: list[Path],
    is_main_context: bool,
    *,
    pre_existing: bool,
) -> bool:
    """Handle extraction failure, cleanup if main context failed.

    Returns True if the entire release should be marked as failed, False otherwise.

    Args:
        logger: Logger for error messages
        target_dir: Directory that failed to extract
        extracted_targets: All directories extracted for this release
        is_main_context: Whether this was the main archive (vs subfolder)
        pre_existing: Whether target_dir existed before extraction

    Returns:
        True if entire release should be marked as failed
    """
    cleanup_failed_extraction_dir(target_dir, pre_existing=pre_existing)

    if is_main_context:
        logger.error(
            "Main archive extraction failed - cleaning up all extracted content for this release"
        )
        for extracted_path in extracted_targets:
            try:
                if extracted_path.exists():
                    shutil.rmtree(str(extracted_path))
            except OSError:
                pass
        return True  # Mark release as failed
    return False


def remove_empty_tree(directory: Path, *, stop: Path) -> None:
    """Remove empty directories walking up the tree.

    Args:
        directory: Starting directory
        stop: Stop at this directory (don't remove it)
    """
    if not directory.exists():
        return

    current = directory
    while current != stop and current.exists():
        try:
            next(current.iterdir())
            break
        except StopIteration:
            try:
                current.rmdir()
            except OSError:
                break
            current = current.parent


def flatten_single_subdir(directory: Path) -> None:
    """If directory contains exactly one subdirectory and no files, move its contents up one level.

    This is useful for archives that extract to a nested directory structure.

    Args:
        directory: Directory to flatten
    """
    try:
        entries = [p for p in directory.iterdir()]
    except OSError:
        return

    files = [p for p in entries if p.is_file()]
    dirs = [p for p in entries if p.is_dir()]

    # Only flatten if there are no files and exactly one subdirectory
    if files:
        return
    if len(dirs) != 1:
        return

    only = dirs[0]
    try:
        children = list(only.iterdir())
        for child in children:
            dest_name = child.name
            dest = directory / dest_name
            counter = 1
            while dest.exists():
                if child.is_dir():
                    dest = directory / f"{dest_name}_{counter}"
                else:
                    stem, suffix = (
                        dest_name.rsplit(".", 1)
                        if "." in dest_name
                        else (dest_name, "")
                    )
                    dest = (
                        directory / f"{stem}_{counter}.{suffix}"
                        if suffix
                        else directory / f"{stem}_{counter}"
                    )
                counter += 1
            shutil.move(str(child), str(dest))
        only.rmdir()
    except OSError:
        pass


def flatten_new_top_level_dirs(target_dir: Path, previous_names: set[str]) -> None:
    """Flatten any newly created top-level directories in target_dir.

    After extracting an episode archive, many release archives create a
    subdirectory named like the archive and put the actual media files inside.
    For single-season/no-season shows, we want files directly under the show
    folder, not one subfolder per episode. This function compares the
    pre-extraction top-level entries with the post-extraction ones, and for
    any newly created directory, moves its contents up one level and removes
    the now-empty directory.
    """
    try:
        current_names = {p.name for p in target_dir.iterdir()}
    except OSError:
        return

    from ..extraction.archive_constants import EPISODE_ONLY_TAG_RE

    # Prefer newly created directories, but also flatten episode-named folders that may already exist
    candidates = set()
    candidates.update(current_names - previous_names)
    for name in current_names:
        if EPISODE_ONLY_TAG_RE.search(name):
            candidates.add(name)

    for name in sorted(candidates):
        candidate = target_dir / name
        if not candidate.is_dir():
            continue
        # Skip known special folders
        lower = name.lower()
        if lower in {"subs", "sub", "sample", "sonstige"}:
            continue
        try:
            # Move all children up one level
            for child in list(candidate.iterdir()):
                dest = ensure_unique_destination(target_dir / child.name)
                try:
                    shutil.move(str(child), str(dest))
                except OSError:
                    pass
            # Remove the now-empty directory (ignore if not empty)
            try:
                candidate.rmdir()
            except OSError:
                pass
        except OSError:
            continue


def _is_video_file(path: Path) -> bool:
    return path.suffix.lower() in {".mkv", ".mp4", ".avi", ".mov", ".m4v"}


def flatten_episode_like_dirs(target_dir: Path) -> None:
    """Flatten any episode-like directories inside target_dir.

    Heuristic: directory name contains episode tag (E01/E001) OR the directory
    directly contains at least one video file. Moves files up and removes the
    directory if it becomes empty.
    """
    from ..extraction.archive_constants import EPISODE_ONLY_TAG_RE

    try:
        top = list(target_dir.iterdir())
    except OSError:
        return

    for candidate in top:
        if not candidate.is_dir():
            continue
        name = candidate.name
        try:
            children = list(candidate.iterdir())
        except OSError:
            continue

        # Consider as episode-like if name has episode tag OR contains any video file
        # either directly or nested deeper (some archives add extra subfolders).
        direct_video = any(_is_video_file(c) for c in children if c.is_file())
        nested_video = False
        if not direct_video:
            try:
                for root, _dirs, files in os.walk(candidate):
                    if any(_is_video_file(Path(root) / f) for f in files):
                        nested_video = True
                        break
            except OSError:
                nested_video = False
        looks_like_episode = (
            EPISODE_ONLY_TAG_RE.search(name) is not None or direct_video or nested_video
        )
        if not looks_like_episode:
            continue

        def _move_up_recursive(current: Path) -> None:
            try:
                for entry in list(current.iterdir()):
                    if entry.is_dir():
                        _move_up_recursive(entry)
                        # Try to remove if empty after recursion
                        try:
                            next(entry.iterdir())
                        except StopIteration:
                            try:
                                entry.rmdir()
                            except OSError:
                                pass
                        continue
                    # File: move to top-level
                    dest = ensure_unique_destination(target_dir / entry.name)
                    try:
                        shutil.move(str(entry), str(dest))
                    except OSError:
                        pass
            except OSError:
                return

        _move_up_recursive(candidate)

        # Attempt to remove top candidate dir if empty
        try:
            next(candidate.iterdir())
        except StopIteration:
            try:
                candidate.rmdir()
            except OSError:
                pass


def copy_non_archives_to_extracted(current_dir: Path, target_dir: Path) -> None:
    """Copy non-archive companion files (e.g. .nfo, .srt) from source to extracted.

    Source files remain in place and will be moved to finished later if extraction succeeds.
    Files are overwritten if they already exist.

    Args:
        current_dir: Source directory
        target_dir: Target directory for copied files
    """
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        for entry in sorted(current_dir.iterdir(), key=lambda p: p.name.lower()):
            if entry.is_file() and not is_supported_archive(entry):
                # Skip unwanted companions like .sfv
                if entry.suffix.lower() == ".sfv":
                    continue
                try:
                    # Copy and overwrite existing files (do not remove source)
                    dest_path = target_dir / entry.name
                    shutil.copy2(str(entry), str(dest_path))

                except OSError as e:
                    _logger = logging.getLogger(__name__)
                    _logger.error("Error copying %s: %s", entry, e)
    except OSError:
        pass


def move_archive_group(
    files: Sequence[Path],
    finished_root: Path,
    relative_parent: Path,
    *,
    tracker: ProgressTracker | None = None,
    logger: logging.Logger | None = None,
) -> list[Path]:
    """Move a group of archive files to the finished directory.

    Args:
        files: Archive files to move
        finished_root: Root of finished directory
        relative_parent: Relative path within finished directory
        tracker: Optional progress tracker
        logger: Optional logger for progress updates

    Returns:
        List of moved file paths
    """
    destination_dir = finished_root / relative_parent
    destination_dir.mkdir(parents=True, exist_ok=True)
    moved: list[Path] = []

    for index, src in enumerate(files, 1):
        destination = ensure_unique_destination(destination_dir / src.name)

        # Use safe move with retry strategies for Docker/UNC paths
        if _safe_move_with_retry(src, destination, logger):
            moved_path = destination

        else:
            # Move failed completely, skip this file
            if logger is not None:
                logger.error("Failed to move %s to %s", src, destination)
            continue
        moved.append(moved_path)
        if tracker is not None and logger is not None:
            tracker.advance(logger, f"Moved {src.name}", absolute=index)

    return moved


def move_remaining_to_finished(
    current_dir: Path,
    *,
    finished_root: Path,
    download_root: Path,
) -> None:
    """Mirror files from a release directory in downloads to finished 1:1.

    All files under the release root in downloads are moved into
    finished/<release_root_name>/, preserving the relative subfolder structure.

    Args:
        current_dir: A directory within a release (often the release root itself)
        finished_root: Root of finished directory
        download_root: Root of downloads directory
    """
    # Determine the release root as the first path segment under download_root
    try:
        rel_parts = current_dir.relative_to(download_root).parts
        if not rel_parts:
            return
        release_root_name = rel_parts[0]
        release_root = download_root / release_root_name
    except ValueError:
        # current_dir is not under download_root; fall back to using its top name
        release_root = current_dir
        release_root_name = current_dir.name

    try:
        for root, _dirs, files in os.walk(current_dir):
            root_path = Path(root)
            try:
                sub_rel = root_path.relative_to(release_root)
            except ValueError:
                sub_rel = Path("")
            dest_dir = finished_root / release_root_name / sub_rel
            dest_dir.mkdir(parents=True, exist_ok=True)
            for fname in files:
                src_file = root_path / fname
                dest = ensure_unique_destination(dest_dir / fname)
                if not _safe_move_with_retry(src_file, dest):
                    _logger = logging.getLogger(__name__)
                    _logger.error("Failed to move %s to %s", src_file, dest)
    except OSError:
        pass


def move_extracted_to_finished(
    extracted_dir: Path,
    *,
    extracted_root: Path,
    finished_root: Path,
) -> None:
    """Move all files from an extracted directory into finished, preserving structure.

    This preserves the relative path under extracted_root and mirrors it under finished_root.

    Args:
        extracted_dir: Directory under extracted_root whose contents should be moved
        extracted_root: Root of the extracted tree
        finished_root: Root of the finished tree
    """
    try:
        rel = extracted_dir.relative_to(extracted_root)
    except ValueError:
        # If not under extracted_root, fall back to using just the directory name
        rel = Path(extracted_dir.name)

    try:
        for root, _dirs, files in os.walk(extracted_dir):
            root_path = Path(root)
            try:
                sub_rel = root_path.relative_to(extracted_dir)
            except ValueError:
                sub_rel = Path("")
            dest_dir = finished_root / rel / sub_rel
            dest_dir.mkdir(parents=True, exist_ok=True)
            for fname in files:
                src_file = root_path / fname
                dest = ensure_unique_destination(dest_dir / fname)
                if not _safe_move_with_retry(src_file, dest):
                    _logger = logging.getLogger(__name__)
                    _logger.error("Failed to move %s to %s", src_file, dest)
    except OSError:
        pass


def is_file_complete(file_path: Path, db: "SettingsDB", stability_hours: int = 24) -> bool:
    """Check if a file is complete by comparing with previous run.
    
    This function checks if a file is completely downloaded by:
    1. Comparing file size with previous run (stored in DB)
    2. Checking if file hasn't been modified recently (stability_hours)
    
    Works for all file types.
    
    Args:
        file_path: Path to the file to check
        db: SettingsDB instance for storing/retrieving file status
        stability_hours: Hours file must be unchanged to be considered complete (default: 24)
    
    Returns:
        True if file appears to be complete, False if still downloading
    """
    if not file_path.exists() or not file_path.is_file():
        return False
    
    try:
        stat = file_path.stat()
        current_size = stat.st_size
        current_mtime = stat.st_mtime
        
        # Get previous status from DB
        prev_status = db.get_file_status(str(file_path))
        
        if prev_status is None:
            # First time seeing this file - save status and assume incomplete
            db.save_file_status(str(file_path), current_size)
            return False
        
        prev_size, last_check = prev_status
        
        # If size changed, still downloading
        if current_size != prev_size:
            db.save_file_status(str(file_path), current_size)
            return False
        
        # Size unchanged - check if file hasn't been modified recently (stability_hours)
        time_since_modification = time.time() - current_mtime
        stability_seconds = stability_hours * 3600
        
        if time_since_modification < stability_seconds:
            # File was modified recently, likely still downloading
            return False
        
        # Size unchanged and file stable for stability_hours - complete
        return True
        
    except (OSError, PermissionError) as e:
        import logging
        logging.getLogger(__name__).debug(f"Failed to check file completeness: {e}")
        return False


__all__ = [
    "ensure_unique_destination",
    "cleanup_failed_extraction_dir",
    "handle_extraction_failure",
    "remove_empty_tree",
    "flatten_single_subdir",
    "copy_non_archives_to_extracted",
    "move_archive_group",
    "move_remaining_to_finished",
    "move_extracted_to_finished",
    "is_file_complete",
]


def move_related_episode_artifacts(
    episode_dir: Path, *, finished_root: Path, download_root: Path
) -> None:
    """Move related artifacts (Subs/Sample/Sonstige/Proof) for a TV episode.

    Looks at sibling directories of the episode directory and moves files that
    match the episode tag (E01/E001) into the corresponding destination under
    finished, preserving structure.

    This avoids leaving behind subtitles or samples stored in sibling folders.
    """
    from ..extraction.archive_constants import EPISODE_ONLY_TAG_RE

    match = EPISODE_ONLY_TAG_RE.search(episode_dir.name)
    if not match:
        return
    episode_tag = match.group(0).lower()

    parent = episode_dir.parent
    try:
        siblings = [p for p in parent.iterdir() if p.is_dir()]
    except OSError:
        return

    related_names = {"subs", "sub", "sample", "sonstige", "proof"}

    for sib in siblings:
        if sib == episode_dir:
            continue
        if sib.name.strip().lower() not in related_names:
            continue
        # Walk sib and move only files that include the episode tag
        try:
            for root, _dirs, files in os.walk(sib):
                root_path = Path(root)
                for fname in files:
                    if episode_tag not in fname.lower():
                        continue
                    src_file = root_path / fname
                    # Compute destination based on the episode_dir
                    try:
                        rel_parts = episode_dir.relative_to(download_root).parts
                        if not rel_parts:
                            continue
                        release_root_name = rel_parts[0]
                        release_root = download_root / release_root_name
                        try:
                            sub_rel = episode_dir.relative_to(release_root)
                        except ValueError:
                            sub_rel = Path("")
                        # Put artifacts next to episode files under the same sub_rel
                        dest_dir = finished_root / release_root_name / sub_rel
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        dest = ensure_unique_destination(dest_dir / fname)
                        _safe_move_with_retry(src_file, dest)
                    except ValueError:
                        continue
        except OSError:
            continue
