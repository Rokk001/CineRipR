"""File and directory operations for archive processing."""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Sequence

from .archive_detection import is_supported_archive
from .progress import ProgressTracker


def ensure_unique_destination(destination: Path) -> Path:
    """Ensure a file doesn't overwrite existing files by appending a counter.
    
    Args:
        destination: Desired destination path
        
    Returns:
        Unique destination path (original or with _N suffix)
    """
    if not destination.exists():
        return destination

    suffix = "".join(destination.suffixes)
    base_name = destination.name[: -len(suffix)] if suffix else destination.name
    counter = 1
    while True:
        candidate = destination.with_name(f"{base_name}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


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
                    stem, suffix = dest_name.rsplit(".", 1) if "." in dest_name else (dest_name, "")
                    dest = directory / f"{stem}_{counter}.{suffix}" if suffix else directory / f"{stem}_{counter}"
                counter += 1
            shutil.move(str(child), str(dest))
        only.rmdir()
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
                    shutil.copy2(str(entry), str(dest_path))
                except OSError:
                    pass
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
        moved_path = Path(shutil.move(str(src), str(destination)))
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
    
    This is independent of extraction policy. The destination mirrors the
    original download structure beneath finished_root.
    
    Args:
        current_dir: Source directory
        finished_root: Root of finished directory
        download_root: Root of downloads directory
    """

    def move_file(src_file: Path) -> None:
        rel_parent = src_file.parent.relative_to(download_root)
        dest_dir = finished_root / rel_parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        try:
            dest = ensure_unique_destination(dest_dir / src_file.name)
            shutil.move(str(src_file), str(dest))
        except OSError:
            pass

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



