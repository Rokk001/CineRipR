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

from .config import Paths
from .progress import format_progress

_logger = logging.getLogger(__name__)


def _build_supported_suffixes() -> tuple[str, ...]:
    suffixes: set[str] = set()
    for _name, suffix_list, _description in shutil.get_unpack_formats():
        for suffix in suffix_list:
            suffixes.add(suffix.lower())
    return tuple(sorted(suffixes, key=len, reverse=True))


SUPPORTED_ARCHIVE_SUFFIXES: tuple[str, ...] = _build_supported_suffixes()
_PART_VOLUME_RE = re.compile(r"^(?P<base>.+?)\.part(?P<index>\d+)(?P<ext>(?:\.[^.]+)+)$", re.IGNORECASE)
_R_VOLUME_RE = re.compile(r"^(?P<base>.+?)\.r(?P<index>\d+)$", re.IGNORECASE)
_SPLIT_EXT_RE = re.compile(r"^(?P<base>.+?)(?P<ext>(?:\.[^.]+)+)\.(?P<index>\d+)$", re.IGNORECASE)


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
        if any(candidate.endswith(suffix) for suffix in SUPPORTED_ARCHIVE_SUFFIXES) or candidate.endswith(".rar"):
            return True

    if _R_VOLUME_RE.match(name):
        return True

    split_match = _SPLIT_EXT_RE.match(name)
    if split_match:
        candidate = f"{split_match.group('base')}{split_match.group('ext')}"
        if any(candidate.endswith(suffix) for suffix in SUPPORTED_ARCHIVE_SUFFIXES) or candidate.endswith(".rar"):
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


def _compute_archive_group_key(archive: Path) -> tuple[str, int]:
    lower_name = archive.name.lower()

    if lower_name.endswith(".rar"):
        return lower_name, -1

    part_match = _PART_VOLUME_RE.match(lower_name)
    if part_match:
        base = f"{part_match.group('base')}{part_match.group('ext')}"
        part_index = int(part_match.group('index') or 0)
        return base, max(part_index, 0)

    r_match = _R_VOLUME_RE.match(lower_name)
    if r_match:
        base = f"{r_match.group('base')}.rar"
        part_index = int(r_match.group('index') or 0)
        return base, max(part_index, 0)

    split_match = _SPLIT_EXT_RE.match(lower_name)
    if split_match:
        base = f"{split_match.group('base')}{split_match.group('ext')}"
        part_index = int(split_match.group('index') or 0)
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
        groups.append(ArchiveGroup(key=key, primary=primary, members=ordered_paths, order_map=order_map))

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
                return False, "missing volume index(es): " + ", ".join(str(value) for value in missing)
        if group.key.endswith(".rar") and not any(order < 0 for order in orders.values()):
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


def can_extract_archive(archive: Path, *, seven_zip_path: Path | None) -> tuple[bool, str | None]:
    format_name = _detect_archive_format(archive)
    if format_name == "rar":
        command = resolve_seven_zip_command(seven_zip_path)
        if command is None:
            return False, "7-Zip executable not found. Configure [tools].seven_zip or install 7-Zip."
        return True, None

    if format_name == "zip":
        try:
            with zipfile.ZipFile(archive) as zf:
                damaged = zf.testzip()
                if damaged is not None:
                    return False, f"corrupt member: {damaged}"
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)
        return True, None

    if format_name in {"tar", "gztar", "bztar", "xztar"}:
        try:
            with tarfile.open(archive) as tf:
                for _member in tf:
                    pass
        except Exception as exc:  # noqa: BLE001
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


def _extract_with_seven_zip(command: str, archive: Path, target_dir: Path) -> None:
def _cleanup_failed_extraction_dir(target_dir: Path, *, pre_existing: bool) -> None:
    if pre_existing:
        return
    try:
        if target_dir.exists() and target_dir.is_dir() and not any(target_dir.iterdir()):
            target_dir.rmdir()
    except OSError:
        pass
    target_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [command, "x", str(archive), f"-o{target_dir}", "-y"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise RuntimeError(
            f"7-Zip extraction failed (exit code {result.returncode})" + (f": {stderr}" if stderr else "")
        )


def extract_archive(archive: Path, target_dir: Path, *, seven_zip_path: Path | None) -> None:
    format_name = _detect_archive_format(archive)
    if format_name == "rar":
        command = resolve_seven_zip_command(seven_zip_path)
        if command is None:
            raise RuntimeError("7-Zip executable not found. Configure [tools].seven_zip or install 7-Zip.")
        _extract_with_seven_zip(command, archive, target_dir)
    else:
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.unpack_archive(str(archive), str(target_dir))


def move_archive_group(files: Sequence[Path], finished_root: Path, relative_parent: Path) -> list[Path]:
    destination_dir = finished_root / relative_parent
    destination_dir.mkdir(parents=True, exist_ok=True)
    moved: list[Path] = []
    for src in files:
        destination = ensure_unique_destination(destination_dir / src.name)
        moved.append(Path(shutil.move(str(src), str(destination))))
    return moved


def process_downloads(
    paths: Paths,
    *,
    demo_mode: bool,
    seven_zip_path: Path | None,
) -> ProcessResult:
    if not SUPPORTED_ARCHIVE_SUFFIXES and seven_zip_path is None:
        raise RuntimeError("No supported archive formats available in the Python standard library.")

    processed = 0
    failed: list[Path] = []
    unsupported: list[Path] = []

    for subdir in iter_download_subdirs(paths.download_root):
        archives, unsupported_entries = split_directory_entries(subdir)
        unsupported.extend(unsupported_entries)
        if not archives:
            _logger.debug("No supported archives found in %s", subdir)
            continue

        groups = build_archive_groups(archives)
        relative_parent = subdir.relative_to(paths.download_root)
        target_dir = paths.extracted_root / relative_parent


        total_groups = len(groups)
        for index, group in enumerate(groups, 1):
            progress = format_progress(index, total_groups)

            complete, reason = validate_archive_group(group)
            if not complete:
                _logger.warning("%s Skipping %s: %s", progress, group.primary, reason)
                failed.append(group.primary)
                continue

            if demo_mode:
                _logger.info(
                    "%s Demo: would extract %s (%s file(s)) to %s",
                    progress,
                    group.primary,
                    group.part_count,
                    target_dir,
                )
            else:
                can_extract, reason = can_extract_archive(group.primary, seven_zip_path=seven_zip_path)
                if not can_extract:
                    _logger.error(
                        "%s Pre-extraction check failed for %s: %s",
                        progress,
                        group.primary,
                        reason,
                    )
                    failed.append(group.primary)
                    continue

                _logger.info(
                    "%s Extracting %s (%s file(s)) to %s",
                    progress,
                    group.primary,
                    group.part_count,
                    target_dir,
                )
                pre_existing_target = target_dir.exists()
                try:
                    extract_archive(group.primary, target_dir, seven_zip_path=seven_zip_path)
                except (shutil.ReadError, RuntimeError) as exc:
                    _logger.error("Extract failed for %s: %s", group.primary, exc)
                    _cleanup_failed_extraction_dir(target_dir, pre_existing=pre_existing_target)
                    failed.append(group.primary)
                    continue
                except Exception:  # noqa: BLE001
                    _logger.exception("Unexpected error while extracting %s", group.primary)
                    _cleanup_failed_extraction_dir(target_dir, pre_existing=pre_existing_target)
                    failed.append(group.primary)
                    continue

            destination_dir = paths.finished_root / relative_parent
            if demo_mode:
                _logger.info(
                    "%s Demo: would move %s file(s) for archive %s to %s",
                    progress,
                    group.part_count,
                    group.primary,
                    destination_dir,
                )
            else:
                _logger.info(
                    "%s Moving %s file(s) for archive %s to %s",
                    progress,
                    group.part_count,
                    group.primary,
                    destination_dir,
                )
                try:
                    move_archive_group(group.members, paths.finished_root, relative_parent)
                except Exception:  # noqa: BLE001
                    _logger.exception("Failed to move archive %s to the finished directory", group.primary)
                    failed.append(group.primary)
                    continue

            processed += 1

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


