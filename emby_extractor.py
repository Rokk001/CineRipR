"""Utility for extracting and cleaning downloaded archives.

Update the paths, demo mode, and retention period in CONFIG before running.
"""

from __future__ import annotations

import logging
import re
import shutil
import tarfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

CONFIG = {
    "download_root": r"C:\\CHANGE_ME\\Download",
    "extracted_root": r"C:\\CHANGE_ME\\Extracted",
    "finished_root": r"C:\\CHANGE_ME\\Finished",
    "finished_retention_days": 14,
    "enable_delete": False,
    "demo_mode": False,
}


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


@dataclass
class Paths:
    download_root: Path
    extracted_root: Path
    finished_root: Path

    @classmethod
    def from_raw(cls, raw: dict[str, object]) -> "Paths":
        required = ("download_root", "extracted_root", "finished_root")
        missing = [key for key in required if key not in raw]
        if missing:
            raise KeyError(f"Missing configuration keys: {', '.join(missing)}")

        path_values: dict[str, Path] = {}
        for key in required:
            value = raw[key]
            if not isinstance(value, (str, Path)):
                raise TypeError(f"Config value for '{key}' must be a string-like path.")
            path_values[key] = Path(value).expanduser()

        for key, path in path_values.items():
            if "CHANGE_ME" in str(path):
                raise ValueError(f"Please update the path for '{key}' in CONFIG.")
        return cls(**path_values)

    def ensure_ready(self) -> None:
        if not self.download_root.exists():
            raise FileNotFoundError(f"Download directory '{self.download_root}' does not exist.")
        if not self.download_root.is_dir():
            raise NotADirectoryError(f"Download path '{self.download_root}' is not a directory.")
        for target in (self.extracted_root, self.finished_root):
            target.mkdir(parents=True, exist_ok=True)


def read_retention_days(raw: dict[str, object]) -> int:
    key = "finished_retention_days"
    if key not in raw:
        raise KeyError("Missing configuration key: finished_retention_days")

    try:
        days = int(raw[key])
    except (TypeError, ValueError) as exc:
        raise ValueError("finished_retention_days must be an integer number of days") from exc

    if days < 0:
        raise ValueError("finished_retention_days must not be negative")
    return days


def read_bool(raw: dict[str, object], key: str, *, default: bool = False) -> bool:
    if key not in raw:
        return default

    value = raw[key]
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False

    raise ValueError(f"Cannot interpret '{key}' as boolean (value: {value!r})")


@dataclass
class Settings:
    paths: Paths
    retention_days: int
    enable_delete: bool
    demo_mode: bool

    @classmethod
    def from_raw(cls, raw: dict[str, object]) -> "Settings":
        paths = Paths.from_raw(raw)
        retention_days = read_retention_days(raw)
        enable_delete = read_bool(raw, "enable_delete", default=False)
        demo_mode = read_bool(raw, "demo_mode", default=False)
        return cls(paths=paths, retention_days=retention_days, enable_delete=enable_delete, demo_mode=demo_mode)


@dataclass
class ArchiveGroup:
    key: str
    primary: Path
    members: tuple[Path, ...]
    order_map: dict[Path, int]

    @property
    def part_count(self) -> int:
        return len(self.members)


def _format_progress(current: int, total: int, *, width: int = 20) -> str:
    if total <= 0:
        return f"[{'-' * width}] 0% (0/0)"
    ratio = max(0.0, min(1.0, current / total))
    filled = int(ratio * width)
    if current > 0 and filled == 0:
        filled = 1
    bar = "#" * filled + "-" * (width - filled)
    percent = int(round(ratio * 100))
    return f"[{bar}] {percent:3d}% ({current}/{total})"


def _log_path_summary(log_fn, label: str, paths: list[Path], *, limit: int = 5) -> None:
    if not paths:
        return
    sorted_paths = sorted(paths, key=lambda path: str(path).lower())
    log_fn("%s (%s)", label, len(sorted_paths))
    for path in sorted_paths[:limit]:
        log_fn("  %s", path)
    remaining = len(sorted_paths) - limit
    if remaining > 0:
        log_fn("  ... %s more", remaining)


def _is_supported_archive(entry: Path) -> bool:
    name = entry.name.lower()
    if any(name.endswith(suffix) for suffix in SUPPORTED_ARCHIVE_SUFFIXES):
        return True

    part_match = _PART_VOLUME_RE.match(name)
    if part_match:
        candidate = f"{part_match.group('base')}{part_match.group('ext')}"
        if any(candidate.endswith(suffix) for suffix in SUPPORTED_ARCHIVE_SUFFIXES):
            return True

    if _R_VOLUME_RE.match(name):
        return True  # treated as part of a .rar set

    split_match = _SPLIT_EXT_RE.match(name)
    if split_match:
        candidate = f"{split_match.group('base')}{split_match.group('ext')}"
        if any(candidate.endswith(suffix) for suffix in SUPPORTED_ARCHIVE_SUFFIXES):
            return True

    return False


def _iter_download_subdirs(download_root: Path) -> Iterator[Path]:
    for entry in sorted(download_root.iterdir(), key=lambda path: path.name.lower()):
        if entry.is_dir():
            yield entry


def _split_directory_entries(directory: Path) -> tuple[list[Path], list[Path]]:
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

    part_match = _PART_VOLUME_RE.match(lower_name)
    if part_match:
        base = f"{part_match.group('base')}{part_match.group('ext')}"
        try:
            part_index = int(part_match.group('index'))
        except ValueError:
            part_index = 0
        return base, max(part_index, 0)

    r_match = _R_VOLUME_RE.match(lower_name)
    if r_match:
        base = f"{r_match.group('base')}.rar"
        try:
            part_index = int(r_match.group('index'))
        except ValueError:
            part_index = 0
        return base, max(part_index, 0)

    split_match = _SPLIT_EXT_RE.match(lower_name)
    if split_match:
        base = f"{split_match.group('base')}{split_match.group('ext')}"
        try:
            part_index = int(split_match.group('index'))
        except ValueError:
            part_index = 0
        return base, max(part_index, 0)

    return lower_name, -1


def _build_archive_groups(archives: list[Path]) -> list[ArchiveGroup]:
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


def _validate_archive_group(group: ArchiveGroup) -> tuple[bool, str | None]:
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
    for format_name, suffixes, _description in shutil.get_unpack_formats():
        for suffix in suffixes:
            if lower.endswith(suffix.lower()):
                return format_name
    return None


def _can_extract_archive(archive: Path) -> tuple[bool, str | None]:
    format_name = _detect_archive_format(archive)
    if format_name == "zip":
        try:
            with zipfile.ZipFile(archive) as zf:
                damaged = zf.testzip()
                if damaged is not None:
                    return False, f"corrupt member: {damaged}"
        except Exception as exc:  # noqa: BLE001 - want details in log
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

    # Unknown format: rely on extraction attempt
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


def extract_archive(archive: Path, target_dir: Path) -> None:
    shutil.unpack_archive(str(archive), str(target_dir))


def move_archive_group(files: tuple[Path, ...], finished_root: Path, relative_parent: Path) -> list[Path]:
    destination_dir = finished_root / relative_parent
    destination_dir.mkdir(parents=True, exist_ok=True)
    moved: list[Path] = []
    for src in files:
        destination = ensure_unique_destination(destination_dir / src.name)
        moved.append(Path(shutil.move(str(src), str(destination))))
    return moved


def process_downloads(paths: Paths, *, demo_mode: bool) -> tuple[int, list[Path], list[Path]]:
    if not SUPPORTED_ARCHIVE_SUFFIXES:
        raise RuntimeError("No supported archive formats available in the Python standard library.")

    processed = 0
    failed: list[Path] = []
    unsupported: list[Path] = []

    for subdir in _iter_download_subdirs(paths.download_root):
        archives, unsupported_entries = _split_directory_entries(subdir)
        unsupported.extend(unsupported_entries)
        if not archives:
            logging.debug("No supported archives found in %s", subdir)
            continue

        groups = _build_archive_groups(archives)
        relative_parent = subdir.relative_to(paths.download_root)
        target_dir = paths.extracted_root / relative_parent

        if not demo_mode:
            target_dir.mkdir(parents=True, exist_ok=True)

        total_groups = len(groups)
        for index, group in enumerate(groups, 1):
            progress = _format_progress(index, total_groups)

            complete, reason = _validate_archive_group(group)
            if not complete:
                logging.warning("%s Skipping %s: %s", progress, group.primary, reason)
                failed.append(group.primary)
                continue

            if demo_mode:
                logging.info(
                    "%s Demo: would extract %s (%s file(s)) to %s",
                    progress,
                    group.primary,
                    group.part_count,
                    target_dir,
                )
            else:
                can_extract, reason = _can_extract_archive(group.primary)
                if not can_extract:
                    logging.error(
                        "%s Pre-extraction check failed for %s: %s",
                        progress,
                        group.primary,
                        reason,
                    )
                    failed.append(group.primary)
                    continue

                logging.info(
                    "%s Extracting %s (%s file(s)) to %s",
                    progress,
                    group.primary,
                    group.part_count,
                    target_dir,
                )
                try:
                    extract_archive(group.primary, target_dir)
                except shutil.ReadError as exc:
                    logging.error("Extract failed for %s: %s", group.primary, exc)
                    failed.append(group.primary)
                    continue
                except Exception:
                    logging.exception("Unexpected error while extracting %s", group.primary)
                    failed.append(group.primary)
                    continue

            destination_dir = paths.finished_root / relative_parent
            if demo_mode:
                logging.info(
                    "%s Demo: would move %s file(s) for archive %s to %s",
                    progress,
                    group.part_count,
                    group.primary,
                    destination_dir,
                )
            else:
                logging.info(
                    "%s Moving %s file(s) for archive %s to %s",
                    progress,
                    group.part_count,
                    group.primary,
                    destination_dir,
                )
                try:
                    move_archive_group(group.members, paths.finished_root, relative_parent)
                except Exception:
                    logging.exception("Failed to move archive %s to the finished directory", group.primary)
                    failed.append(group.primary)
                    continue

            processed += 1

    return processed, failed, unsupported


def cleanup_finished(
    finished_root: Path,
    retention_days: int,
    *,
    enable_delete: bool,
    demo_mode: bool,
) -> tuple[list[Path], list[Path], list[Path]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted: list[Path] = []
    failed: list[Path] = []
    skipped: list[Path] = []
    candidate_directories: set[Path] = set()

    for file_path in finished_root.rglob("*"):
        if not file_path.is_file():
            continue

        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
        if file_mtime > cutoff:
            continue

        if demo_mode:
            logging.info("Demo mode: would delete %s", file_path)
            skipped.append(file_path)
            continue

        if not enable_delete:
            logging.info("Delete switch disabled: skipping deletion of %s", file_path)
            skipped.append(file_path)
            continue

        try:
            file_path.unlink()
        except Exception:
            logging.exception("Could not delete %s", file_path)
            failed.append(file_path)
            continue

        deleted.append(file_path)
        candidate_directories.add(file_path.parent)

    if enable_delete and not demo_mode:
        for directory in sorted(candidate_directories, key=lambda path: len(path.parts), reverse=True):
            if directory == finished_root:
                continue
            try:
                directory.rmdir()
            except OSError:
                continue

    return deleted, failed, skipped


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        settings = Settings.from_raw(CONFIG)
    except Exception as exc:
        logging.error("Configuration error: %s", exc)
        return 1

    try:
        settings.paths.ensure_ready()
    except Exception as exc:
        logging.error("Path validation failed: %s", exc)
        return 1

    if settings.demo_mode:
        logging.warning("Demo mode enabled: no files will be extracted, moved, or deleted.")
    elif not settings.enable_delete:
        logging.info("Delete switch disabled: finished cleanup will not remove files.")

    try:
        processed, failed, unsupported = process_downloads(settings.paths, demo_mode=settings.demo_mode)
    except Exception as exc:
        logging.error("Processing error: %s", exc)
        return 1

    deleted, cleanup_failed, skipped_cleanup = cleanup_finished(
        settings.paths.finished_root,
        settings.retention_days,
        enable_delete=settings.enable_delete,
        demo_mode=settings.demo_mode,
    )

    logging.info("Processed archives: %s", processed)
    if settings.demo_mode:
        logging.info("Demo mode: all actions were simulated only.")

    _log_path_summary(logging.error, "Failed archives", failed)
    _log_path_summary(logging.warning, "Unsupported files", unsupported)
    _log_path_summary(logging.info, "Deleted finished files", deleted)
    _log_path_summary(logging.info, "Skipped finished files", skipped_cleanup)
    _log_path_summary(logging.error, "Failed to clean finished directory", cleanup_failed)

    if failed or cleanup_failed:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
