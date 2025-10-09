"""File and directory operations for archive processing."""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Sequence

from .archive_detection import is_supported_archive
from .progress import ProgressTracker


def _set_file_permissions(path: Path) -> None:
    """Set file permissions to 777.

    Args:
        path: File or directory path to set permissions for
    """
    try:
        # Set permissions to 777 (read/write/execute for all)
        path.chmod(0o777)
    except (OSError, ImportError):
        pass


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
        _set_file_permissions(dst)

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
            _set_file_permissions(normalized_dst)
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

    from .archive_constants import EPISODE_ONLY_TAG_RE

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
    from .archive_constants import EPISODE_ONLY_TAG_RE

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
                    # Copy and overwrite existing files
                    dest_path = target_dir / entry.name
                    # Use safe copy with retry strategies for Docker/UNC paths
                    if _safe_move_with_retry(entry, dest_path):
                        # Fix permissions for copied files (important for Docker environments)
                        _set_file_permissions(dest_path)
                    else:
                        _logger = logging.getLogger(__name__)
                        _logger.error("Failed to copy %s to %s", entry, dest_path)
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
            # Set proper permissions for moved files
            _set_file_permissions(moved_path)
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
    """Move all remaining files (any type) under current_dir to finished.

    For TV shows, this uses the proper TV-Show structure from README:
    TV-Shows/Show Name/Season XX/

    For movies and other content, this mirrors the original download structure.

    Args:
        current_dir: Source directory
        finished_root: Root of finished directory
        download_root: Root of downloads directory
    """
    from .path_utils import looks_like_tv_show, build_tv_show_path, get_category_prefix

    def move_file(src_file: Path) -> None:
        # Determine if this is a TV show based on the extracted directory structure
        is_tv_show = looks_like_tv_show(current_dir)

        if is_tv_show:
            # For TV shows, use the proper structure from README
            try:
                # Get the category prefix (TV-Shows)
                category_prefix = get_category_prefix(current_dir)

                # Build the proper TV show path using the existing logic
                tv_show_path = build_tv_show_path(
                    current_dir, download_root, category_prefix
                )
                dest_dir = finished_root / tv_show_path
            except (ValueError, OSError):
                # Fallback to simple structure if TV show path building fails
                try:
                    rel_path = src_file.parent.relative_to(download_root)
                    release_name = rel_path.parts[-1] if rel_path.parts else "unknown"
                except ValueError:
                    release_name = (
                        src_file.parent.name if src_file.parent.name else "unknown"
                    )
                dest_dir = finished_root / release_name
        else:
            # For movies and other content, use the original logic
            try:
                rel_path = src_file.parent.relative_to(download_root)
                release_name = rel_path.parts[-1] if rel_path.parts else "unknown"
            except ValueError:
                # File is not under download_root (e.g., in extracted directory)
                # Try to extract release name from the file path itself
                path_parts = src_file.parts
                # Look for common patterns in the path to extract release name
                for part in path_parts:
                    # Look for parts that might be release names (contain dots, dashes, etc.)
                    if "." in part and any(char.isdigit() for char in part):
                        # This looks like a release name, use it
                        release_name = part
                        break
                else:
                    # Fallback: use the parent directory name
                    release_name = (
                        src_file.parent.name if src_file.parent.name else "unknown"
                    )
            dest_dir = finished_root / release_name

        dest_dir.mkdir(parents=True, exist_ok=True)
        try:
            dest = ensure_unique_destination(dest_dir / src_file.name)

            # Use safe move with retry strategies for Docker/UNC paths
            if _safe_move_with_retry(src_file, dest):
                # Set proper permissions for moved files
                _set_file_permissions(dest)
            else:
                # Log error if move completely failed
                _logger = logging.getLogger(__name__)
                _logger.error("Failed to move %s to %s", src_file, dest)

        except OSError as e:
            _logger = logging.getLogger(__name__)
            _logger.error("Error moving %s: %s", src_file, e)

    try:
        for root, _dirs, files in os.walk(current_dir):
            root_path = Path(root)
            for fname in files:
                move_file(root_path / fname)
    except OSError:
        pass


__all__ = [
    "ensure_unique_destination",
    "cleanup_failed_extraction_dir",
    "handle_extraction_failure",
    "remove_empty_tree",
    "flatten_single_subdir",
    "copy_non_archives_to_extracted",
    "move_archive_group",
    "move_remaining_to_finished",
]
