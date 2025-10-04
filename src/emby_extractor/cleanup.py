"""Finished directory cleanup utilities."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

_logger = logging.getLogger(__name__)


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

        try:
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
        except FileNotFoundError:  # pragma: no cover - race condition
            continue

        if file_mtime > cutoff:
            continue

        if demo_mode:
            _logger.info("Demo mode: would delete %s", file_path)
            skipped.append(file_path)
            continue

        if not enable_delete:
            _logger.info("Delete switch disabled: skipping deletion of %s", file_path)
            skipped.append(file_path)
            continue

        try:
            file_path.unlink()
        except Exception:  # noqa: BLE001
            _logger.exception("Could not delete %s", file_path)
            failed.append(file_path)
            continue

        deleted.append(file_path)
        candidate_directories.add(file_path.parent)

    if enable_delete and not demo_mode:
        _remove_empty_directories(candidate_directories, finished_root)

    return deleted, failed, skipped


def _remove_empty_directories(candidate_directories: Iterable[Path], finished_root: Path) -> None:
    for directory in sorted(set(candidate_directories), key=lambda path: len(path.parts), reverse=True):
        if directory == finished_root:
            continue
        try:
            directory.rmdir()
        except OSError:
            continue


__all__ = ["cleanup_finished"]
