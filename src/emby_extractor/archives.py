"""Archive discovery, validation and extraction helpers."""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence

from .config import Paths, SubfolderPolicy
from .progress import format_progress, ProgressTracker

_logger = logging.getLogger(__name__)


def _build_supported_suffixes() -> tuple[str, ...]:
    suffixes: set[str] = set()
    for _name, suffix_list, _description in shutil.get_unpack_formats():
        for suffix in suffix_list:
            suffixes.add(suffix.lower())
    return tuple(sorted(suffixes, key=len, reverse=True))


SUPPORTED_ARCHIVE_SUFFIXES: tuple[str, ...] = _build_supported_suffixes()
_PART_VOLUME_RE = re.compile(
    r"^(?P<base>.+?)\.part(?P<index>\d+)(?P<ext>(?:\.[^.]+)+)$", re.IGNORECASE
)
_R_VOLUME_RE = re.compile(r"^(?P<base>.+?)\.r(?P<index>\d+)$", re.IGNORECASE)
_SPLIT_EXT_RE = re.compile(
    r"^(?P<base>.+?)(?P<ext>(?:\.[^.]+)+)\.(?P<index>\d+)$", re.IGNORECASE
)


@dataclass(frozen=True)
class ArchiveGroup:
    """Represents a collection of files belonging to the same archive."""

    key: str
    primary: Path
    members: tuple[Path, ...]
    order_map: dict[Path, int]

    @property
    def part_count(self) -> int:
        return len(self.members)


@dataclass(frozen=True)
class ProcessResult:
    processed: int
    failed: list[Path]
    unsupported: list[Path]


def _is_supported_archive(entry: Path) -> bool:
    name = entry.name.lower()
    if name.endswith(".rar"):
        return True
    if any(name.endswith(suffix) for suffix in SUPPORTED_ARCHIVE_SUFFIXES):
        return True

    part_match = _PART_VOLUME_RE.match(name)
    if part_match:
        candidate = f"{part_match.group('base')}{part_match.group('ext')}"
        if any(
            candidate.endswith(suffix) for suffix in SUPPORTED_ARCHIVE_SUFFIXES
        ) or candidate.endswith(".rar"):
            return True

    if _R_VOLUME_RE.match(name):
        return True

    split_match = _SPLIT_EXT_RE.match(name)
    if split_match:
        candidate = f"{split_match.group('base')}{split_match.group('ext')}"
        if any(
            candidate.endswith(suffix) for suffix in SUPPORTED_ARCHIVE_SUFFIXES
        ) or candidate.endswith(".rar"):
            return True

    return False


def iter_download_subdirs(download_root: Path) -> Iterator[Path]:
    for entry in sorted(download_root.iterdir(), key=lambda path: path.name.lower()):
        if entry.is_dir():
            yield entry


def split_directory_entries(directory: Path) -> tuple[list[Path], list[Path]]:
    supported: list[Path] = []
    unsupported: list[Path] = []
    for entry in sorted(directory.iterdir(), key=lambda path: path.name.lower()):
        if not entry.is_file():
            continue
        if _is_supported_archive(entry):
            supported.append(entry)
        else:
            unsupported.append(entry)
    return supported, unsupported


def _iter_release_directories(
    base_dir: Path, download_root: Path, policy: SubfolderPolicy
) -> list[tuple[Path, Path, bool]]:
    contexts: list[tuple[Path, Path, bool]] = []

    def _contains_supported_archives(directory: Path) -> bool:
        try:
            for entry in directory.iterdir():
                if entry.is_file() and _is_supported_archive(entry):
                    return True
        except OSError:
            return False
        return False

    def _is_season_dir(path: Path) -> bool:
        name = path.name.strip().lower()
        return bool(re.match(r"^season\s*\d+$", name))

    def _normalize_special_subdir(name: str) -> str | None:
        lower = name.strip().lower()
        if lower in {"sub", "subs", "untertitel"}:
            return "Subs"
        if lower == "sample":
            return "Sample"
        if lower in {"sonstige", "other", "misc"}:
            return "Sonstige"
        return None

    def _append(directory: Path, relative_parent: Path, should_extract: bool) -> None:
        contexts.append((directory, relative_parent, should_extract))

    # Determine whether this release looks like a TV show (has Season xx) or a Movie
    has_season_child = False
    try:
        for child in base_dir.iterdir():
            if child.is_dir() and _is_season_dir(child):
                has_season_child = True
                break
    except OSError:
        has_season_child = False
    base_prefix = (
        Path("TV-Shows")
        if has_season_child or _is_season_dir(base_dir)
        else Path("Movies")
    )

    # Always consider the release root itself, prefixed by category
    _append(base_dir, base_prefix / base_dir.relative_to(download_root), True)

    for child in sorted(base_dir.iterdir(), key=lambda path: path.name.lower()):
        if not child.is_dir():
            continue

        child_name = child.name
        normalized = _normalize_special_subdir(child_name)

        # Decide if we should extract this child dir
        contains_archives = _contains_supported_archives(child)
        contains_any_files = False
        try:
            contains_any_files = any(p.is_file() for p in child.iterdir())
        except OSError:
            contains_any_files = False
        if normalized == "Sample":
            should_extract = policy.include_sample or contains_archives
        elif normalized == "Subs":
            should_extract = policy.include_sub or contains_archives
        elif normalized == "Sonstige":
            should_extract = policy.include_other or contains_archives
        else:
            should_extract = policy.include_other or contains_archives

        # Series flattening: if this looks like Season/.../<episode_dir>, extract into the Season folder
        if _is_season_dir(base_dir) and (contains_archives or contains_any_files):
            season_rel = base_prefix / base_dir.relative_to(download_root)
            _append(child, season_rel, should_extract)
            continue

        # For normalized special subdirs, map the relative parent to the normalized name
        if normalized is not None:
            rel = base_prefix / base_dir.relative_to(download_root) / normalized
            _append(child, rel, should_extract)
            continue

        # Default: mirror structure
        _append(child, base_prefix / child.relative_to(download_root), should_extract)

    return contexts


def _ensure_standard_subdirs(extracted_root: Path, relative_parent: Path) -> None:
    base = extracted_root / relative_parent
    # Create normalized standard subdirectories for movies
    for name in ("Subs", "Sample", "Sonstige"):
        try:
            (base / name).mkdir(parents=True, exist_ok=True)
        except OSError:
            # Non-fatal: creation might fail due to permissions
            pass


def _compute_archive_group_key(archive: Path) -> tuple[str, int]:
    lower_name = archive.name.lower()

    if lower_name.endswith(".rar"):
        return lower_name, -1

    part_match = _PART_VOLUME_RE.match(lower_name)
    if part_match:
        base = f"{part_match.group('base')}{part_match.group('ext')}"
        part_index = int(part_match.group("index") or 0)
        return base, max(part_index, 0)

    r_match = _R_VOLUME_RE.match(lower_name)
    if r_match:
        base = f"{r_match.group('base')}.rar"
        part_index = int(r_match.group("index") or 0)
        return base, max(part_index, 0)

    split_match = _SPLIT_EXT_RE.match(lower_name)
    if split_match:
        base = f"{split_match.group('base')}{split_match.group('ext')}"
        part_index = int(split_match.group("index") or 0)
        return base, max(part_index, 0)

    return lower_name, -1


def build_archive_groups(archives: Sequence[Path]) -> list[ArchiveGroup]:
    grouped: dict[str, list[tuple[int, Path]]] = {}
    for archive in archives:
        key, order = _compute_archive_group_key(archive)
        grouped.setdefault(key, []).append((order, archive))

    groups: list[ArchiveGroup] = []
    for key, items in grouped.items():
        items.sort(key=lambda item: (item[0], item[1].name.lower()))
        ordered_paths = tuple(path for _order, path in items)
        order_map = {path: order for order, path in items}
        primary = ordered_paths[0]
        groups.append(
            ArchiveGroup(
                key=key, primary=primary, members=ordered_paths, order_map=order_map
            )
        )

    groups.sort(key=lambda group: group.primary.name.lower())
    return groups


def validate_archive_group(group: ArchiveGroup) -> tuple[bool, str | None]:
    orders = group.order_map
    positives = sorted(order for order in orders.values() if order >= 0)
    if positives:
        start = 0 if 0 in positives else 1 if 1 in positives else positives[0]
        expected = list(range(start, start + len(positives)))
        if positives != expected:
            missing = sorted(set(expected) - set(positives))
            if missing:
                return False, "missing volume index(es): " + ", ".join(
                    str(value) for value in missing
                )
        if group.key.endswith(".rar") and not any(
            order < 0 for order in orders.values()
        ):
            return False, "missing base .rar volume"

    if not group.primary.exists():
        return False, "primary archive file is missing"

    return True, None


def _detect_archive_format(archive: Path) -> str | None:
    lower = archive.name.lower()
    if lower.endswith(".rar"):
        return "rar"
    for format_name, suffixes, _description in shutil.get_unpack_formats():
        for suffix in suffixes:
            if lower.endswith(suffix.lower()):
                return format_name
    return None


def resolve_seven_zip_command(seven_zip_path: Path | None) -> str | None:
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

    for name in ("7z", "7za", "7zr"):
        resolved = shutil.which(name)
        if resolved:
            return resolved
    return None


def can_extract_archive(
    archive: Path, *, seven_zip_path: Path | None
) -> tuple[bool, str | None]:
    format_name = _detect_archive_format(archive)
    if format_name == "rar":
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


def ensure_unique_destination(destination: Path) -> Path:
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


def _cleanup_failed_extraction_dir(target_dir: Path, *, pre_existing: bool) -> None:
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


def _remove_empty_tree(directory: Path, *, stop: Path) -> None:
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


def _extract_with_seven_zip(
    command: str,
    archive: Path,
    target_dir: Path,
    *,
    progress: ProgressTracker | None = None,
) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    # Use -bb1 for basic progress and stream stdout for parsing percentage lines
    process = subprocess.Popen(
        [command, "x", str(archive), f"-o{target_dir}", "-y", "-bsp1", "-bso1", "-bb1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    if process.stdout is None:
        stdout_lines: list[str] = []
    else:
        stdout_lines = []
        for line in process.stdout:
            stdout_lines.append(line)
            if progress is not None:
                text = line.strip()
                # Typical 7z progress lines contain percentages like " 12%"
                m = re.search(r"(\d{1,3})%", text)
                if m:
                    if progress.total > 0:
                        percent = max(0, min(100, int(m.group(1))))
                        current = int(round((percent / 100) * progress.total))
                        progress.advance(
                            _logger,
                            f"Extracting with 7-Zip: {percent}%",
                            absolute=current,
                        )
    process.wait()
    if process.returncode != 0:
        stderr = "".join(stdout_lines).strip()
        raise RuntimeError(
            f"7-Zip extraction failed (exit code {process.returncode})"
            + (f": {stderr}" if stderr else "")
        )


def extract_archive(
    archive: Path,
    target_dir: Path,
    *,
    seven_zip_path: Path | None,
    progress: ProgressTracker | None = None,
) -> None:
    format_name = _detect_archive_format(archive)
    if format_name == "rar":
        command = resolve_seven_zip_command(seven_zip_path)
        if command is None:
            raise RuntimeError(
                "7-Zip executable not found. Configure [tools].seven_zip or install 7-Zip."
            )
        _extract_with_seven_zip(command, archive, target_dir, progress=progress)
    else:
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.unpack_archive(str(archive), str(target_dir))
        if progress is not None:
            progress.complete(_logger, "Finished extracting archive")


def move_archive_group(
    files: Sequence[Path],
    finished_root: Path,
    relative_parent: Path,
    *,
    tracker: ProgressTracker | None = None,
    logger: logging.Logger | None = None,
) -> list[Path]:
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


def process_downloads(
    paths: Paths,
    *,
    demo_mode: bool,
    seven_zip_path: Path | None,
    subfolders: SubfolderPolicy,
) -> ProcessResult:
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
        for current_dir, relative_parent, should_extract in contexts:
            archives, unsupported_entries = split_directory_entries(current_dir)
            unsupported.extend(unsupported_entries)
            if not archives:
                # Handle already-extracted content: copy files to extracted and move to finished
                try:
                    target_dir = paths.extracted_root / relative_parent
                    finished_dir = paths.finished_root / current_dir.relative_to(
                        download_root
                    )
                    target_dir.mkdir(parents=True, exist_ok=True)
                    finished_dir.mkdir(parents=True, exist_ok=True)
                    for entry in sorted(
                        current_dir.iterdir(), key=lambda p: p.name.lower()
                    ):
                        if not entry.is_file():
                            continue
                        # copy to extracted
                        try:
                            shutil.copy2(
                                str(entry),
                                str(ensure_unique_destination(target_dir / entry.name)),
                            )
                        except OSError:
                            pass
                        # move to finished
                        try:
                            destination = ensure_unique_destination(
                                finished_dir / entry.name
                            )
                            shutil.move(str(entry), str(destination))
                        except OSError:
                            pass
                except OSError:
                    pass
                _logger.debug("No supported archives found in %s", current_dir)
                continue

            groups = build_archive_groups(archives)
            target_dir = paths.extracted_root / relative_parent
            finished_relative_parent = current_dir.relative_to(download_root)
            destination_dir = paths.finished_root / finished_relative_parent

            total_groups = len(groups)
            for index, group in enumerate(groups, 1):
                progress_before = format_progress(index - 1, total_groups)

                complete, reason = validate_archive_group(group)
                if not complete:
                    _logger.warning(
                        "%s Skipping %s: %s", progress_before, group.primary, reason
                    )
                    failed.append(group.primary)
                    continue

                part_count = max(group.part_count, 1)
                read_tracker = ProgressTracker(part_count, single_line=True)
                extract_tracker = ProgressTracker(100, single_line=True)
                move_tracker = ProgressTracker(part_count, single_line=True)
                read_tracker.log(
                    _logger,
                    f"Preparing archive {group.primary.name} ({group.part_count} file(s))",
                )

                if should_extract:
                    if demo_mode:
                        for idx, member in enumerate(group.members, 1):
                            read_tracker.advance(
                                _logger,
                                f"Demo: would read {member.name}",
                                absolute=idx,
                            )
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
                        # Finish read tracker
                        read_tracker.complete(_logger, "Finished reading archive parts")

                        pre_existing_target = target_dir.exists()
                        try:
                            extract_archive(
                                group.primary,
                                target_dir,
                                seven_zip_path=seven_zip_path,
                                progress=extract_tracker,
                            )
                        except (shutil.ReadError, RuntimeError) as exc:
                            _logger.error(
                                "Extract failed for %s: %s", group.primary, exc
                            )
                            _cleanup_failed_extraction_dir(
                                target_dir, pre_existing=pre_existing_target
                            )
                            failed.append(group.primary)
                            continue
                        except OSError:
                            _logger.exception(
                                "Unexpected error while extracting %s", group.primary
                            )
                            _cleanup_failed_extraction_dir(
                                target_dir, pre_existing=pre_existing_target
                            )
                            failed.append(group.primary)
                            continue
                        else:
                            extract_tracker.complete(
                                _logger,
                                f"Finished extracting {group.primary.name}",
                            )
                else:
                    read_tracker.complete(
                        _logger,
                        f"Skipping extraction for {group.primary.name} (disabled in configuration)",
                    )

                # Ensure standard subfolders exist under the parent target directory
                try:
                    _ensure_standard_subdirs(paths.extracted_root, relative_parent)
                except OSError:
                    pass

                if demo_mode:
                    move_tracker.log(
                        _logger,
                        f"Preparing to move {group.part_count} file(s) for {group.primary.name}",
                    )
                    for idx, member in enumerate(group.members, 1):
                        move_tracker.advance(
                            _logger,
                            f"Demo: would move {member.name}",
                            absolute=idx,
                        )
                    move_tracker.complete(
                        _logger,
                        f"Finished (demo) moving {group.part_count} file(s) for {group.primary.name}",
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
                            finished_relative_parent,
                            tracker=move_tracker,
                            logger=_logger,
                        )
                    except OSError:
                        _logger.exception(
                            "Failed to move archive %s to the finished directory",
                            group.primary,
                        )
                        failed.append(group.primary)
                        continue
                    else:
                        move_tracker.complete(
                            _logger,
                            f"Finished moving {group.part_count} file(s) to {destination_dir}",
                        )

                processed += 1

                if not demo_mode and not should_extract:
                    _remove_empty_tree(target_dir, stop=paths.extracted_root)

            if not demo_mode and should_extract:
                _remove_empty_tree(target_dir, stop=paths.extracted_root)

            # After finishing this release, remove empty directories under the download root
            if not demo_mode:
                _remove_empty_tree(release_dir, stop=download_root)

    return ProcessResult(processed=processed, failed=failed, unsupported=unsupported)


__all__ = [
    "ArchiveGroup",
    "ProcessResult",
    "SUPPORTED_ARCHIVE_SUFFIXES",
    "process_downloads",
    "move_archive_group",
    "extract_archive",
    "can_extract_archive",
    "validate_archive_group",
    "resolve_seven_zip_command",
]
