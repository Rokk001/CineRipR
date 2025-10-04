"""Utility for extracting and cleaning downloaded archives.

Update the paths, demo mode, and retention period in CONFIG before running.
"""

from __future__ import annotations

import logging
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

CONFIG = {
    "download_root": r"\\hs\Download\dcpp",
    "extracted_root": r"\\hs\Multimedia\Neu\_extracted",
    "finished_root": r"\\hs\Multimedia\Neu\_finished",
    "finished_retention_days": 14,
    "enable_delete": False,
    "demo_mode": True,
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


@dataclass(frozen=True)
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


@dataclass(frozen=True)
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
        lower_name = entry.name.lower()
        if any(lower_name.endswith(suffix) for suffix in SUPPORTED_ARCHIVE_SUFFIXES):
            supported.append(entry)
        else:
            unsupported.append(entry)
    return supported, unsupported


def _compute_archive_group_key(archive: Path) -> tuple[str, int]:
    lower_name = archive.name.lower()

    part_match = _PART_VOLUME_RE.match(lower_name)
    if part_match:
        base = f"{part_match.group('base')}{part_match.group('ext')}"
        part_index = int(part_match.group('index'))
        return base, part_index if part_index >= 0 else 0

    r_match = _R_VOLUME_RE.match(lower_name)
    if r_match:
        base = f"{r_match.group('base')}.rar"
        part_index = int(r_match.group('index'))
        return base, part_index if part_index >= 0 else 0

    split_match = _SPLIT_EXT_RE.match(lower_name)
    if split_match:
        base = f"{split_match.group('base')}{split_match.group('ext')}"
        part_index = int(split_match.group('index'))
        return base, part_index if part_index >= 0 else 0

    return lower_name, -1


def _select_primary_archives(archives: list[Path]) -> list[Path]:
    if not archives:
        return []

    group_min: dict[str, tuple[int, Path]] = {}
    cache: dict[Path, tuple[str, int]] = {}

    for archive in archives:
        key, order = _compute_archive_group_key(archive)
        cache[archive] = (key, order)
        current = group_min.get(key)
        if current is None:
            group_min[key] = (order, archive)
            continue
        current_order, current_path = current
        if order < current_order or (order == current_order and archive.name < current_path.name):
            group_min[key] = (order, archive)

    primary: list[Path] = []
    for archive in archives:
        key, _ = cache[archive]
        if group_min[key][1] == archive:
            primary.append(archive)
    return primary


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


def extract_archive(archive: Path, target_dir: Path, *, demo_mode: bool) -> None:
    if demo_mode:
        logging.info("Demo mode: would extract %s to %s", archive, target_dir)
        return

    logging.info("Extracting %s to %s", archive, target_dir)
    shutil.unpack_archive(str(archive), str(target_dir))


def move_to_finished(archive: Path, finished_root: Path, relative_parent: Path, *, demo_mode: bool) -> None:
    destination_dir = finished_root / relative_parent
    destination = ensure_unique_destination(destination_dir / archive.name)

    if demo_mode:
        logging.info("Demo mode: would move %s to %s", archive, destination)
        return

    destination_dir.mkdir(parents=True, exist_ok=True)
    logging.info("Moving %s to %s", archive, destination)
    shutil.move(str(archive), str(destination))


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

        primary_archives = _select_primary_archives(archives)
        relative_parent = subdir.relative_to(paths.download_root)
        target_dir = paths.extracted_root / relative_parent

        if not demo_mode:
            target_dir.mkdir(parents=True, exist_ok=True)

        for archive in primary_archives:
            try:
                extract_archive(archive, target_dir, demo_mode=demo_mode)
            except shutil.ReadError as exc:
                logging.error("Extract failed for %s: %s", archive, exc)
                failed.append(archive)
                continue
            except Exception:
                logging.exception("Unexpected error while extracting %s", archive)
                failed.append(archive)
                continue

            try:
                move_to_finished(archive, paths.finished_root, relative_parent, demo_mode=demo_mode)
            except Exception:
                logging.exception("Failed to move %s to the finished directory", archive)
                failed.append(archive)
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

    if failed:
        logging.error("Failed archives (%s):", len(failed))
        for item in failed:
            logging.error("  %s", item)
    if unsupported:
        logging.warning("Unsupported files (%s):", len(unsupported))
        for item in unsupported:
            logging.warning("  %s", item)
    if deleted:
        logging.info("Deleted finished files (%s):", len(deleted))
        for item in deleted:
            logging.info("  %s", item)
    if skipped_cleanup:
        logging.info("Skipped finished files (%s):", len(skipped_cleanup))
        for item in skipped_cleanup:
            logging.info("  %s", item)
    if cleanup_failed:
        logging.error("Failed to clean finished directory (%s):", len(cleanup_failed))
        for item in cleanup_failed:
            logging.error("  %s", item)

    if failed or cleanup_failed:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
