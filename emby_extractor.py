"""Utility zum Entpacken und Bereinigen von heruntergeladenen Archiven.

Passe die Pfade und die Aufbewahrungsdauer in CONFIG an deine Umgebung an
und starte das Script.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

CONFIG = {
    "download_root": r"\\hs\Download\dcpp",
    "extracted_root": r"\\hs\Multimedia\Neu\_extracting",
    "finished_root": r"\\hs\Multimedia\Neu\_finished",
    "finished_retention_days": 14,
}


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
                raise ValueError(f"Bitte aktualisiere den Pfad fuer '{key}' in CONFIG.")
        return cls(**path_values)

    def ensure_ready(self) -> None:
        if not self.download_root.exists():
            raise FileNotFoundError(f"Download-Verzeichnis '{self.download_root}' existiert nicht.")
        if not self.download_root.is_dir():
            raise NotADirectoryError(f"Download-Pfad '{self.download_root}' ist kein Verzeichnis.")
        for target in (self.extracted_root, self.finished_root):
            target.mkdir(parents=True, exist_ok=True)


def get_supported_extensions() -> set[str]:
    extensions: set[str] = set()
    for _name, suffixes, _description in shutil.get_unpack_formats():
        for suffix in suffixes:
            extensions.add(suffix.lower())
    return extensions


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


def find_archives(directory: Path, supported_suffixes: set[str]) -> Iterable[Path]:
    for entry in sorted(directory.iterdir()):
        if not entry.is_file():
            continue
        lower_name = entry.name.lower()
        if any(lower_name.endswith(suffix) for suffix in supported_suffixes):
            yield entry


def ensure_unique_destination(destination: Path) -> Path:
    if not destination.exists():
        return destination

    suffix = "".join(destination.suffixes)
    base_name = destination.name[:-len(suffix)] if suffix else destination.name
    counter = 1
    while True:
        candidate = destination.with_name(f"{base_name}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def extract_archive(archive: Path, target_dir: Path) -> None:
    logging.info("Entpacke %s nach %s", archive, target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(archive), str(target_dir))


def move_to_finished(archive: Path, finished_root: Path, relative_parent: Path) -> None:
    destination_dir = finished_root / relative_parent
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = ensure_unique_destination(destination_dir / archive.name)
    logging.info("Verschiebe %s nach %s", archive, destination)
    shutil.move(str(archive), str(destination))


def process_downloads(paths: Paths) -> tuple[int, list[Path], list[Path]]:
    supported_suffixes = get_supported_extensions()
    if not supported_suffixes:
        raise RuntimeError("Keine unterstuetzten Archivformate im Python-Standard vorhanden.")
    processed = 0
    failed: list[Path] = []
    unsupported: list[Path] = []

    for subdir in sorted(paths.download_root.iterdir()):
        if not subdir.is_dir():
            continue

        archives = list(find_archives(subdir, supported_suffixes))
        if not archives:
            logging.debug("Kein unterstuetztes Archiv in %s gefunden", subdir)
            continue

        relative_parent = subdir.relative_to(paths.download_root)
        target_dir = paths.extracted_root / relative_parent

        for archive in archives:
            try:
                extract_archive(archive, target_dir)
            except shutil.ReadError as exc:
                logging.error("Entpacken fehlgeschlagen fuer %s: %s", archive, exc)
                failed.append(archive)
                continue
            except Exception:
                logging.exception("Unerwarteter Fehler beim Entpacken von %s", archive)
                failed.append(archive)
                continue

            try:
                move_to_finished(archive, paths.finished_root, relative_parent)
            except Exception:
                logging.exception("Konnte %s nicht in den Finished-Pfad verschieben", archive)
                failed.append(archive)
                continue

            processed += 1

        for entry in subdir.iterdir():
            if entry.is_file() and entry not in archives:
                lower_name = entry.name.lower()
                if not any(lower_name.endswith(suffix) for suffix in supported_suffixes):
                    unsupported.append(entry)

    return processed, failed, unsupported


def cleanup_finished(finished_root: Path, retention_days: int) -> tuple[list[Path], list[Path]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted: list[Path] = []
    failed: list[Path] = []

    for file_path in sorted(finished_root.rglob("*")):
        if not file_path.is_file():
            continue

        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
        if file_mtime > cutoff:
            continue

        try:
            file_path.unlink()
        except Exception:
            logging.exception("Konnte %s nicht loeschen", file_path)
            failed.append(file_path)
            continue

        deleted.append(file_path)

    # Entferne leere Verzeichnisse, die durch das Aufraeumen entstanden sind
    for directory in sorted({path.parent for path in deleted}, key=lambda p: len(p.parts), reverse=True):
        if directory == finished_root:
            continue
        try:
            directory.rmdir()
        except OSError:
            continue

    return deleted, failed


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        paths = Paths.from_raw(CONFIG)
        retention_days = read_retention_days(CONFIG)
    except Exception as exc:
        logging.error("Konfigurationsfehler: %s", exc)
        return 1

    try:
        paths.ensure_ready()
    except Exception as exc:
        logging.error("Pfadpruefung fehlgeschlagen: %s", exc)
        return 1

    try:
        processed, failed, unsupported = process_downloads(paths)
    except Exception as exc:
        logging.error("Fehler bei der Verarbeitung: %s", exc)
        return 1

    deleted, cleanup_failed = cleanup_finished(paths.finished_root, retention_days)

    logging.info("Verarbeitete Archive: %s", processed)
    if failed:
        logging.error("Fehlgeschlagene Archive (%s):", len(failed))
        for item in failed:
            logging.error("  %s", item)
    if unsupported:
        logging.warning("Nicht unterstuetzte Dateien (%s):", len(unsupported))
        for item in unsupported:
            logging.warning("  %s", item)
    if deleted:
        logging.info("Geloeschte Finished-Dateien (%s):", len(deleted))
        for item in deleted:
            logging.info("  %s", item)
    if cleanup_failed:
        logging.error("Fehler beim Aufraeumen des Finished-Pfades (%s):", len(cleanup_failed))
        for item in cleanup_failed:
            logging.error("  %s", item)

    return 0 if not failed and not cleanup_failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
