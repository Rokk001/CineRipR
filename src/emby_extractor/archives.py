"""Main archive processing orchestration."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from .archive_constants import TV_TAG_RE, SUPPORTED_ARCHIVE_SUFFIXES
from .archive_detection import (
    ArchiveGroup,
    split_directory_entries,
    build_archive_groups,
    validate_archive_group,
)
from .archive_extraction import can_extract_archive, extract_archive
from .file_operations import (
    copy_non_archives_to_extracted,
    flatten_single_subdir,
    handle_extraction_failure,
    move_archive_group,
    move_remaining_to_finished,
    ensure_unique_destination,
)
from .path_utils import (
    is_season_directory,
    build_tv_show_path,
    normalize_special_subdir,
    looks_like_tv_show,
    get_category_prefix,
)
from .config import Paths, SubfolderPolicy
from .progress import ProgressTracker, format_progress, next_progress_color


_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessResult:
    """Result of processing downloads.
    
    Attributes:
        processed: Number of successfully processed archives
        failed: List of archives that failed to process
        unsupported: List of unsupported files encountered
    """
    processed: int
    failed: list[Path]
    unsupported: list[Path]


def iter_download_subdirs(download_root: Path) -> list[Path]:
    """Yield immediate subdirectories under the download root.
    
    Args:
        download_root: Root directory containing downloads
        
    Returns:
        List of subdirectories representing releases
    """
    try:
        return sorted(
            (p for p in download_root.iterdir() if p.is_dir()),
            key=lambda path: path.name.lower(),
        )
    except OSError:
        return []


def _contains_supported_archives(directory: Path) -> bool:
    """Check if a directory contains any supported archive files.
    
    Args:
        directory: Directory to check
        
    Returns:
        True if directory contains archives
    """
    try:
        archives, _ = split_directory_entries(directory)
        return len(archives) > 0
    except OSError:
        return False


def _iter_release_directories(
    base_dir: Path, download_root: Path, policy: SubfolderPolicy
) -> list[tuple[Path, Path, bool]]:
    """Iterate over all contexts (dirs with relative path + extract flag) for a release.

    Process subdirectories first (Subs, Sample, etc.), then the main directory.
    For TV shows with nested episode directories, recursively process them.
    
    Args:
        base_dir: Release root directory
        download_root: Download root path
        policy: Subfolder extraction policy
        
    Returns:
        List of tuples (source_dir, target_relative_path, should_extract)
    """
    contexts: list[tuple[Path, Path, bool]] = []

    base_prefix = get_category_prefix(base_dir)

    # Process all subdirectories first
    for child in sorted(base_dir.iterdir(), key=lambda path: path.name.lower()):
        if not child.is_dir():
            continue

        child_name = child.name
        normalized = normalize_special_subdir(child_name)

        # Check if contains archives or files
        contains_archives = _contains_supported_archives(child)
        contains_any_files = False
        try:
            contains_any_files = any(p.is_file() for p in child.iterdir())
        except OSError:
            contains_any_files = False

        # Determine if we should extract this child dir
        if normalized == "Sample":
            should_extract = policy.include_sample or contains_archives
        elif normalized == "Subs":
            should_extract = policy.include_sub or contains_archives
        elif normalized == "Sonstige":
            should_extract = policy.include_other or contains_archives
        else:
            # For non-normalized subdirs, only extract if include_other is enabled
            should_extract = policy.include_other

        # Series flattening: if this looks like Season/.../<episode_dir>, extract into Season folder
        if is_season_directory(base_dir) and (contains_archives or contains_any_files):
            if should_extract:
                if looks_like_tv_show(base_dir):
                    season_rel = build_tv_show_path(base_dir, download_root, base_prefix)
                else:
                    season_rel = base_prefix / base_dir.relative_to(download_root)
                contexts.append((child, season_rel, should_extract))
            continue

        # For normalized special subdirs, map to normalized name
        if normalized is not None:
            if should_extract:
                if looks_like_tv_show(base_dir):
                    rel = build_tv_show_path(base_dir, download_root, base_prefix) / normalized
                else:
                    rel = base_prefix / base_dir.relative_to(download_root) / normalized
                contexts.append((child, rel, should_extract))
            continue

        # If this child looks like an episode directory, recursively process it
        if TV_TAG_RE.search(child.name) and (contains_archives or contains_any_files):
            child_contexts = _iter_release_directories(child, download_root, policy)
            contexts.extend(child_contexts)
            continue

        # Default: mirror structure
        if should_extract:
            if looks_like_tv_show(base_dir):
                child_rel = build_tv_show_path(child, download_root, base_prefix)
            else:
                child_rel = base_prefix / child.relative_to(download_root)
            contexts.append((child, child_rel, should_extract))

    # Add the main release directory last, but only if it contains archives
    if _contains_supported_archives(base_dir):
        if looks_like_tv_show(base_dir):
            main_rel = build_tv_show_path(base_dir, download_root, base_prefix)
        else:
            main_rel = base_prefix / base_dir.relative_to(download_root)
        contexts.append((base_dir, main_rel, True))

    return contexts


def _remove_empty_subdirs(root: Path) -> None:
    """Remove empty subdirectories from a directory tree."""
    try:
        for directory in sorted(
            (p for p in root.rglob("*") if p.is_dir()),
            key=lambda p: len(p.parts),
            reverse=True,
        ):
            try:
                next(directory.iterdir())
            except StopIteration:
                try:
                    directory.rmdir()
                except OSError:
                    pass
    except OSError:
        pass


def _remove_empty_tree(directory: Path, *, stop: Path) -> None:
    """Remove empty directories walking up the tree until stop."""
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


def process_downloads(
    paths: Paths,
    *,
    demo_mode: bool,
    seven_zip_path: Path | None,
    subfolders: SubfolderPolicy,
) -> ProcessResult:
    """Process all downloads: extract archives and organize files.
    
    Main workflow:
    1. For each release, process subdirectories first (Subs, Sample, etc.)
    2. Then process main archive last
    3. On success, move all archives to finished
    4. On main archive failure, cleanup all extracted content
    
    Args:
        paths: Configuration paths (downloads, extracted, finished)
        demo_mode: If True, don't actually extract/move files
        seven_zip_path: Path to 7-Zip executable (for RAR files)
        subfolders: Policy for which subfolders to process
        
    Returns:
        ProcessResult with counts and failed archives
    """
    if not SUPPORTED_ARCHIVE_SUFFIXES and seven_zip_path is None:
        raise RuntimeError(
            "No supported archive formats available in the Python standard library."
        )

    processed = 0
    failed: list[Path] = []
    unsupported: list[Path] = []

    for download_root in paths.download_roots:
        for release_dir in iter_download_subdirs(download_root):
            contexts = _iter_release_directories(release_dir, download_root, subfolders)

            # Track all extracted targets and archive groups for this release
            extracted_targets: list[Path] = []
            archive_groups_to_move: list[tuple[ArchiveGroup, Path, Path]] = []
            files_to_move: list[tuple[Path, Path]] = []
            release_failed = False
            is_main_context = False

            # Use consistent color for entire release
            release_color = next_progress_color()

            for context_index, (current_dir, relative_parent, should_extract) in enumerate(contexts):
                # Last context is always the main release directory
                is_main_context = context_index == len(contexts) - 1
                
                archives, unsupported_entries = split_directory_entries(current_dir)
                unsupported.extend(unsupported_entries)
                
                if not archives:
                    # Handle directories without archives: copy files to extracted
                    if not demo_mode:
                        try:
                            target_dir = paths.extracted_root / relative_parent
                            target_dir.mkdir(parents=True, exist_ok=True)
                            extracted_targets.append(target_dir)

                            # Count files to copy
                            files_to_copy = [
                                entry
                                for entry in current_dir.iterdir()
                                if entry.is_file() and entry.suffix.lower() != ".sfv"
                            ]

                            if files_to_copy:
                                copy_tracker = ProgressTracker(
                                    len(files_to_copy),
                                    single_line=True,
                                    color=release_color,
                                )
                                copy_tracker.log(
                                    _logger,
                                    f"Copying {len(files_to_copy)} file(s) from {current_dir.name}",
                                )

                                for idx, entry in enumerate(sorted(files_to_copy, key=lambda p: p.name.lower()), 1):
                                    try:
                                        dest_path = target_dir / entry.name
                                        shutil.copy2(str(entry), str(dest_path))
                                        copy_tracker.advance(
                                            _logger,
                                            f"Copied {entry.name}",
                                            absolute=idx,
                                        )
                                    except OSError:
                                        pass

                                copy_tracker.complete(
                                    _logger,
                                    f"Finished copying {len(files_to_copy)} file(s) from {current_dir.name}",
                                )

                            # Mark for moving to finished later
                            finished_relative_parent = current_dir.relative_to(download_root)
                            files_to_move.append((current_dir, finished_relative_parent))
                        except OSError:
                            pass
                    _logger.debug("No supported archives found in %s", current_dir)
                    continue

                # Process archives in this directory
                groups = build_archive_groups(archives)
                target_dir = paths.extracted_root / relative_parent
                finished_relative_parent = current_dir.relative_to(download_root)

                total_groups = len(groups)
                for index, group in enumerate(groups, 1):
                    progress_before = format_progress(index - 1, total_groups)

                    complete, reason = validate_archive_group(group)
                    if not complete:
                        _logger.warning("%s Skipping %s: %s", progress_before, group.primary, reason)
                        failed.append(group.primary)
                        continue

                    part_count = max(group.part_count, 1)
                    read_tracker = ProgressTracker(part_count, single_line=True, color=release_color)
                    extract_tracker = ProgressTracker(100, single_line=True, color=release_color)
                    
                    read_tracker.log(
                        _logger,
                        f"Preparing archive {group.primary.name} ({group.part_count} file(s))",
                    )
                    read_tracker.advance(
                        _logger,
                        f"Preparing archive {group.primary.name} ({group.part_count} file(s))",
                        absolute=part_count,
                    )

                    extracted_ok = False
                    if should_extract:
                        if demo_mode:
                            for idx, member in enumerate(group.members, 1):
                                read_tracker.advance(
                                    _logger,
                                    f"Demo: would read {member.name}",
                                    absolute=idx,
                                )
                            extracted_ok = True
                        else:
                            can_extract, reason = can_extract_archive(
                                group.primary, seven_zip_path=seven_zip_path
                            )
                            if not can_extract:
                                _logger.error(
                                    "%s Pre-extraction check failed for %s: %s",
                                    progress_before,
                                    group.primary,
                                    reason,
                                )
                                failed.append(group.primary)
                                continue

                            for idx, member in enumerate(group.members, 1):
                                try:
                                    member.stat()
                                except OSError:
                                    pass
                                read_tracker.advance(
                                    _logger,
                                    f"Reading {member.name}",
                                    absolute=idx,
                                )

                            pre_existing_target = target_dir.exists()
                            try:
                                # Copy companion files
                                copy_non_archives_to_extracted(current_dir, target_dir)
                                
                                # Extract archive
                                extract_archive(
                                    group.primary,
                                    target_dir,
                                    seven_zip_path=seven_zip_path,
                                    progress=extract_tracker,
                                    logger=_logger,
                                )
                            except (shutil.ReadError, RuntimeError) as exc:
                                _logger.error("Extract failed for %s: %s", group.primary, exc)
                                failed.append(group.primary)

                                if handle_extraction_failure(
                                    _logger,
                                    target_dir,
                                    extracted_targets,
                                    is_main_context,
                                    pre_existing=pre_existing_target,
                                ):
                                    release_failed = True
                                    break
                                continue
                            except OSError:
                                _logger.exception("Unexpected error while extracting %s", group.primary)
                                failed.append(group.primary)

                                if handle_extraction_failure(
                                    _logger,
                                    target_dir,
                                    extracted_targets,
                                    is_main_context,
                                    pre_existing=pre_existing_target,
                                ):
                                    release_failed = True
                                    break
                                continue
                            else:
                                # Flatten if needed
                                flatten_single_subdir(target_dir)
                                extract_tracker.complete(
                                    _logger,
                                    f"Finished extracting {group.primary.name}",
                                )
                                extracted_ok = True
                                extracted_targets.append(target_dir)
                    else:
                        read_tracker.complete(
                            _logger,
                            f"Skipping extraction for {group.primary.name} (disabled in configuration)",
                        )

                    # Collect for later move to finished
                    if extracted_ok:
                        archive_groups_to_move.append((group, finished_relative_parent, current_dir))
                        processed += 1

                # Break if release failed
                if release_failed:
                    break

            # Skip to next release if failed
            if release_failed:
                continue

            # Move all archives to finished
            if archive_groups_to_move and not release_failed:
                _logger.info(
                    "All extractions complete for release %s - moving %d archive group(s) to finished",
                    release_dir.name,
                    len(archive_groups_to_move),
                )

                for group, finished_rel_parent, source_dir in archive_groups_to_move:
                    move_tracker = ProgressTracker(group.part_count, single_line=True, color=release_color)
                    destination_dir = paths.finished_root / finished_rel_parent

                    if demo_mode:
                        move_tracker.log(
                            _logger,
                            f"Demo: Would move {group.part_count} file(s) to {destination_dir}",
                        )
                        for idx, member in enumerate(group.members, 1):
                            move_tracker.advance(
                                _logger,
                                f"Demo: would move {member.name}",
                                absolute=idx,
                            )
                        move_tracker.complete(
                            _logger,
                            f"Demo: Finished moving {group.part_count} file(s)",
                        )
                    else:
                        move_tracker.log(
                            _logger,
                            f"Moving {group.part_count} file(s) to {destination_dir}",
                        )
                        try:
                            move_archive_group(
                                group.members,
                                paths.finished_root,
                                finished_rel_parent,
                                tracker=move_tracker,
                                logger=_logger,
                            )
                            move_tracker.complete(
                                _logger,
                                f"Finished moving {group.part_count} file(s) to {destination_dir}",
                            )
                        except OSError:
                            _logger.exception(
                                "Failed to move archive %s to the finished directory",
                                group.primary,
                            )
                            failed.append(group.primary)
                            continue

                # Move remaining companion files
                if not demo_mode:
                    for group, finished_rel_parent, source_dir in archive_groups_to_move:
                        move_remaining_to_finished(
                            source_dir,
                            finished_root=paths.finished_root,
                            download_root=download_root,
                        )
                        _remove_empty_subdirs(source_dir)
                        _remove_empty_tree(source_dir, stop=download_root)

            # Move files that had no archives
            if files_to_move and not release_failed:
                if not demo_mode:
                    for source_dir, finished_rel_parent in files_to_move:
                        try:
                            finished_dir = paths.finished_root / finished_rel_parent
                            finished_dir.mkdir(parents=True, exist_ok=True)
                            for entry in sorted(source_dir.iterdir(), key=lambda p: p.name.lower()):
                                if not entry.is_file():
                                    continue
                                try:
                                    destination = ensure_unique_destination(finished_dir / entry.name)
                                    shutil.move(str(entry), str(destination))
                                except OSError:
                                    pass
                            _remove_empty_subdirs(source_dir)
                            _remove_empty_tree(source_dir, stop=download_root)
                        except OSError:
                            pass

            # Cleanup empty directories
            if not demo_mode:
                _remove_empty_tree(release_dir, stop=download_root)

    return ProcessResult(processed=processed, failed=failed, unsupported=unsupported)


__all__ = [
    "ArchiveGroup",
    "ProcessResult",
    "SUPPORTED_ARCHIVE_SUFFIXES",
    "process_downloads",
]
