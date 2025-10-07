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
    base_dir: Path, download_root: Path, policy: SubfolderPolicy, *, debug: bool = False
) -> list[tuple[Path, Path, bool]]:
    """Iterate over all contexts (dirs with relative path + extract flag) for a release.

    Process subdirectories first (Subs, Sample, etc.), then the main directory.
    For TV shows with nested episode directories, recursively process them.

    Args:
        base_dir: Release root directory
        download_root: Download root path
        policy: Subfolder extraction policy
        debug: If True, output detailed debug information

    Returns:
        List of tuples (source_dir, target_relative_path, should_extract)
    """
    if debug:
        _logger.info("DEBUG: Processing directory: %s", base_dir)
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

        if debug:
            _logger.info(
                "DEBUG:   Child: %s, archives=%s, files=%s, normalized=%s",
                child.name[:50],
                contains_archives,
                contains_any_files,
                normalized,
            )

        # Determine if we should extract this child dir
        if normalized == "Sample":
            should_extract = policy.include_sample or contains_archives
        elif normalized == "Subs":
            should_extract = policy.include_sub or contains_archives
        elif normalized == "Sonstige":
            should_extract = policy.include_other or contains_archives
        else:
            # For episode directories inside Season folders, always extract if they have archives
            if is_season_directory(base_dir) and contains_archives:
                should_extract = True
            else:
                # For other non-normalized subdirs, only extract if include_other is enabled
                should_extract = policy.include_other

        # Series flattening: if this looks like Season/.../<episode_dir>, extract into Season folder
        if is_season_directory(base_dir) and (contains_archives or contains_any_files):
            if debug:
                _logger.info(
                    "DEBUG:   In Season flattening branch, should_extract=%s",
                    should_extract,
                )
            if should_extract:
                if looks_like_tv_show(base_dir):
                    season_rel = build_tv_show_path(
                        base_dir, download_root, base_prefix
                    )
                else:
                    season_rel = base_prefix / base_dir.relative_to(download_root)
                contexts.append((child, season_rel, should_extract))
                if debug:
                    _logger.info("DEBUG:   Added episode to contexts: %s", child.name)
            else:
                if debug:
                    _logger.info(
                        "DEBUG:   Skipped episode (should_extract=False): %s",
                        child.name,
                    )
            continue

        # For normalized special subdirs, map to normalized name
        if normalized is not None:
            if should_extract:
                if looks_like_tv_show(base_dir):
                    rel = (
                        build_tv_show_path(base_dir, download_root, base_prefix)
                        / normalized
                    )
                else:
                    rel = base_prefix / base_dir.relative_to(download_root) / normalized
                contexts.append((child, rel, should_extract))
            continue

        # If this child is a Season directory, recursively process its episode directories
        if is_season_directory(child):
            if debug:
                _logger.info(
                    "DEBUG: Found Season directory: %s, recursing...", child.name
                )
            child_contexts = _iter_release_directories(
                child, download_root, policy, debug=debug
            )
            if debug:
                _logger.info(
                    "DEBUG: Season %s returned %d contexts",
                    child.name,
                    len(child_contexts),
                )
            contexts.extend(child_contexts)
            continue

        # If this child looks like an episode directory, recursively process it
        has_tv_tag = TV_TAG_RE.search(child.name) is not None
        if debug:
            _logger.info(
                "DEBUG:   TV_TAG match for '%s': %s", child.name[:50], has_tv_tag
            )
        if has_tv_tag and (contains_archives or contains_any_files):
            if debug:
                _logger.info(
                    "DEBUG: Found episode directory: %s, recursing...", child.name
                )
            child_contexts = _iter_release_directories(
                child, download_root, policy, debug=debug
            )
            if debug:
                _logger.info(
                    "DEBUG: Episode %s returned %d contexts",
                    child.name,
                    len(child_contexts),
                )
            contexts.extend(child_contexts)
            continue

        # Default: mirror structure
        if debug:
            _logger.info("DEBUG:   Default branch: should_extract=%s", should_extract)
        if should_extract:
            if looks_like_tv_show(base_dir):
                child_rel = build_tv_show_path(child, download_root, base_prefix)
            else:
                child_rel = base_prefix / child.relative_to(download_root)
            contexts.append((child, child_rel, should_extract))
            if debug:
                _logger.info(
                    "DEBUG:   Added to contexts: %s -> %s", child.name, child_rel
                )

    # Add the main release directory last, but only if it contains archives
    if _contains_supported_archives(base_dir):
        if looks_like_tv_show(base_dir):
            main_rel = build_tv_show_path(base_dir, download_root, base_prefix)
        else:
            main_rel = base_prefix / base_dir.relative_to(download_root)
        contexts.append((base_dir, main_rel, True))

    if debug:
        _logger.info(
            "DEBUG: Returning %d contexts for %s", len(contexts), base_dir.name
        )
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
    cpu_cores: int = 2,
    debug: bool = False,
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
        cpu_cores: Number of CPU cores to use for extraction (default: 2)
        debug: If True, output detailed debug information (default: False)

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
            contexts = _iter_release_directories(
                release_dir, download_root, subfolders, debug=debug
            )

            # Track all extracted targets and archive groups for this release
            extracted_targets: list[Path] = []
            archive_groups_to_move: list[tuple[ArchiveGroup, Path, Path]] = []
            files_to_move: list[tuple[Path, Path]] = []
            release_failed = False
            is_main_context = False

            # Track current context color (changes per episode/film)
            context_color = next_progress_color()
            last_episode_name: str | None = None

            for context_index, (
                current_dir,
                relative_parent,
                should_extract,
            ) in enumerate(contexts):
                # Last context is always the main release directory
                is_main_context = context_index == len(contexts) - 1

                # Determine the episode/film directory (not subfolders like Subs)
                # If current_dir is a subfolder (Subs, Sample), use parent as episode
                episode_dir = current_dir
                if current_dir.parent != release_dir and current_dir.name in (
                    "Subs",
                    "Sample",
                    "Sonstige",
                    "Proof",
                ):
                    episode_dir = current_dir.parent

                # Change color only when we encounter a new episode/film
                episode_name = episode_dir.name
                if context_index > 0 and episode_name != last_episode_name:
                    context_color = next_progress_color()

                # Remember the episode name for next iteration
                last_episode_name = episode_name

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
                                    color=context_color,
                                )
                                copy_tracker.log(
                                    _logger,
                                    f"Copying {len(files_to_copy)} file(s) from {current_dir.name}",
                                )

                                for idx, entry in enumerate(
                                    sorted(files_to_copy, key=lambda p: p.name.lower()),
                                    1,
                                ):
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
                            finished_relative_parent = current_dir.relative_to(
                                download_root
                            )
                            files_to_move.append(
                                (current_dir, finished_relative_parent)
                            )
                        except OSError:
                            pass
                    _logger.debug("No supported archives found in %s", current_dir)
                    continue

                # Process archives in this directory
                groups = build_archive_groups(archives)
                target_dir = paths.extracted_root / relative_parent
                finished_relative_parent = current_dir.relative_to(download_root)

                # Calculate total parts across all groups for unified progress tracking
                total_parts = sum(group.part_count for group in groups)
                total_groups = len(groups)

                # Initial announcement - complete immediately
                announce_tracker = ProgressTracker(
                    1, single_line=True, color=context_color
                )
                announce_tracker.complete(
                    _logger,
                    f"Processing {total_groups} archive(s) with {total_parts} file(s)...",
                )

                # Tracker for extraction phase
                extract_tracker = ProgressTracker(
                    total_groups, single_line=True, color=context_color
                )

                parts_processed = 0
                extractions_done = 0

                # Phase 1: Validate and read all groups first
                groups_to_extract: list[tuple[int, ArchiveGroup]] = []

                for index, group in enumerate(groups, 1):
                    progress_before = format_progress(index - 1, total_groups)

                    complete, reason = validate_archive_group(group)
                    if not complete:
                        _logger.warning(
                            "%s Skipping %s: %s", progress_before, group.primary, reason
                        )
                        failed.append(group.primary)
                        continue

                    if should_extract:
                        if demo_mode:
                            # Read all parts silently (no progress updates)
                            for member in group.members:
                                parts_processed += 1

                            # Show completion message only
                            _logger.info(
                                "%s Demo: Finished reading %s",
                                format_progress(
                                    group.part_count,
                                    group.part_count,
                                    color=context_color,
                                ),
                                group.primary.name,
                            )
                            groups_to_extract.append((index, group))
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

                            # Read all parts silently (no progress updates)
                            for member in group.members:
                                try:
                                    member.stat()
                                except OSError:
                                    pass
                                parts_processed += 1

                            # Show completion message only
                            _logger.info(
                                "%s Finished reading %s",
                                format_progress(
                                    group.part_count,
                                    group.part_count,
                                    color=context_color,
                                ),
                                group.primary.name,
                            )

                            groups_to_extract.append((index, group))
                    else:
                        # Skip extraction but still count parts as processed
                        parts_processed += group.part_count
                        _logger.info(
                            "Skipping extraction for %s (disabled in configuration)",
                            group.primary.name,
                        )

                # Phase 2: Extract all groups
                for index, group in groups_to_extract:
                    pre_existing_target = target_dir.exists()
                    extracted_ok = False

                    try:
                        # Copy companion files
                        copy_non_archives_to_extracted(current_dir, target_dir)

                        # Create a progress tracker for this specific extraction
                        extraction_progress = ProgressTracker(
                            group.part_count, single_line=True, color=context_color
                        )

                        # Extract archive with progress tracking
                        extract_archive(
                            group.primary,
                            target_dir,
                            seven_zip_path=seven_zip_path,
                            cpu_cores=cpu_cores,
                            progress=extraction_progress,
                            logger=_logger,
                            part_count=group.part_count,
                        )

                        # Count extraction as done
                        extractions_done += 1

                        # Flatten if needed
                        flatten_single_subdir(target_dir)
                        extracted_ok = True
                        extracted_targets.append(target_dir)

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
                        _logger.exception(
                            "Unexpected error while extracting %s",
                            group.primary,
                        )
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

                    # Collect for later move to finished
                    if extracted_ok:
                        archive_groups_to_move.append(
                            (group, finished_relative_parent, current_dir)
                        )
                        processed += 1

                # Complete extraction phase
                if extractions_done > 0:
                    extract_tracker.complete(
                        _logger,
                        f"Extracted {extractions_done} archive(s) for {current_dir.name}",
                    )
                    # Prepare a fresh color for the next film/episode context
                    # so that subsequent progress bars switch color at boundaries
                    context_color = next_progress_color()

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

                # Calculate total files to move across all groups
                total_files_to_move = sum(
                    group.part_count for group, _, _ in archive_groups_to_move
                )

                # Create a single tracker for all moves in this release
                # Use a new color for the move phase
                move_color = next_progress_color()
                move_tracker = ProgressTracker(
                    total_files_to_move, single_line=True, color=move_color
                )

                if demo_mode:
                    move_tracker.log(
                        _logger,
                        f"Demo: Would move {total_files_to_move} file(s) for release {release_dir.name}",
                    )
                else:
                    move_tracker.log(
                        _logger,
                        f"Moving {total_files_to_move} file(s) for release {release_dir.name}",
                    )

                files_moved = 0
                for group, finished_rel_parent, source_dir in archive_groups_to_move:
                    destination_dir = paths.finished_root / finished_rel_parent

                    if demo_mode:
                        for idx, member in enumerate(group.members, 1):
                            files_moved += 1
                            move_tracker.advance(
                                _logger,
                                f"Demo: would move {member.name}",
                                absolute=files_moved,
                            )
                    else:
                        try:
                            for member in group.members:
                                destination = ensure_unique_destination(
                                    destination_dir / member.name
                                )
                                destination_dir.mkdir(parents=True, exist_ok=True)
                                shutil.move(str(member), str(destination))
                                files_moved += 1
                                move_tracker.advance(
                                    _logger,
                                    f"Moved {member.name}",
                                    absolute=files_moved,
                                )
                        except OSError:
                            _logger.exception(
                                "Failed to move archive %s to the finished directory",
                                group.primary,
                            )
                            failed.append(group.primary)
                            continue

                # Complete the move tracker once for all files
                move_tracker.complete(
                    _logger,
                    f"Finished moving {total_files_to_move} file(s) for release {release_dir.name}",
                )

                # Move remaining companion files
                if not demo_mode:
                    for (
                        group,
                        finished_rel_parent,
                        source_dir,
                    ) in archive_groups_to_move:
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
                            for entry in sorted(
                                source_dir.iterdir(), key=lambda p: p.name.lower()
                            ):
                                if not entry.is_file():
                                    continue
                                try:
                                    destination = ensure_unique_destination(
                                        finished_dir / entry.name
                                    )
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
