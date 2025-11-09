"""Status tracking for WebGUI."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ProcessingStatus:
    """Current processing status for a single operation."""

    release_name: str
    current_archive: str | None = None
    archive_progress: int = 0
    archive_total: int = 0
    status: str = "idle"  # idle, scanning, extracting, moving, completed, failed
    message: str = ""
    error: str | None = None


@dataclass
class GlobalStatus:
    """Global status tracking for the entire application."""

    is_running: bool = False
    current_operation: str = "idle"
    processed_count: int = 0
    failed_count: int = 0
    unsupported_count: int = 0
    deleted_count: int = 0
    cleanup_failed_count: int = 0
    last_update: datetime = field(default_factory=datetime.now)
    current_release: ProcessingStatus | None = None
    recent_logs: list[dict[str, Any]] = field(default_factory=list)
    start_time: datetime | None = None
    last_completion_time: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert status to dictionary for JSON serialization."""
        return {
            "is_running": self.is_running,
            "current_operation": self.current_operation,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "unsupported_count": self.unsupported_count,
            "deleted_count": self.deleted_count,
            "cleanup_failed_count": self.cleanup_failed_count,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "current_release": (
                {
                    "release_name": self.current_release.release_name,
                    "current_archive": self.current_release.current_archive,
                    "archive_progress": self.current_release.archive_progress,
                    "archive_total": self.current_release.archive_total,
                    "status": self.current_release.status,
                    "message": self.current_release.message,
                    "error": self.current_release.error,
                }
                if self.current_release
                else None
            ),
            "recent_logs": self.recent_logs[-50:],  # Last 50 logs
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_completion_time": (
                self.last_completion_time.isoformat()
                if self.last_completion_time
                else None
            ),
        }


class StatusTracker:
    """Thread-safe status tracker for WebGUI."""

    def __init__(self) -> None:
        self._status = GlobalStatus()
        self._lock = threading.Lock()

    def start_processing(self) -> None:
        """Mark processing as started."""
        with self._lock:
            self._status.is_running = True
            self._status.start_time = datetime.now()
            self._status.current_operation = "processing"
            self._status.last_update = datetime.now()

    def stop_processing(self) -> None:
        """Mark processing as stopped."""
        with self._lock:
            self._status.is_running = False
            self._status.current_operation = "idle"
            self._status.last_completion_time = datetime.now()
            self._status.last_update = datetime.now()

    def set_current_release(self, release_name: str) -> None:
        """Set the current release being processed."""
        with self._lock:
            self._status.current_release = ProcessingStatus(release_name=release_name)
            self._status.last_update = datetime.now()

    def update_release_status(
        self,
        status: str,
        message: str = "",
        current_archive: str | None = None,
        archive_progress: int = 0,
        archive_total: int = 0,
        error: str | None = None,
    ) -> None:
        """Update the current release status."""
        with self._lock:
            if self._status.current_release:
                self._status.current_release.status = status
                self._status.current_release.message = message
                self._status.current_release.current_archive = current_archive
                self._status.current_release.archive_progress = archive_progress
                self._status.current_release.archive_total = archive_total
                self._status.current_release.error = error
            self._status.last_update = datetime.now()

    def add_log(self, level: str, message: str) -> None:
        """Add a log entry."""
        with self._lock:
            self._status.recent_logs.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": level,
                    "message": message,
                }
            )
            # Keep only last 100 logs
            if len(self._status.recent_logs) > 100:
                self._status.recent_logs = self._status.recent_logs[-100:]
            self._status.last_update = datetime.now()

    def update_counts(
        self,
        processed: int | None = None,
        failed: int | None = None,
        unsupported: int | None = None,
        deleted: int | None = None,
        cleanup_failed: int | None = None,
    ) -> None:
        """Update processing counts."""
        with self._lock:
            if processed is not None:
                self._status.processed_count = processed
            if failed is not None:
                self._status.failed_count = failed
            if unsupported is not None:
                self._status.unsupported_count = unsupported
            if deleted is not None:
                self._status.deleted_count = deleted
            if cleanup_failed is not None:
                self._status.cleanup_failed_count = cleanup_failed
            self._status.last_update = datetime.now()

    def get_status(self) -> GlobalStatus:
        """Get a copy of the current status."""
        with self._lock:
            # Return a copy to avoid race conditions
            status = GlobalStatus(
                is_running=self._status.is_running,
                current_operation=self._status.current_operation,
                processed_count=self._status.processed_count,
                failed_count=self._status.failed_count,
                unsupported_count=self._status.unsupported_count,
                deleted_count=self._status.deleted_count,
                cleanup_failed_count=self._status.cleanup_failed_count,
                last_update=self._status.last_update,
                current_release=(
                    ProcessingStatus(
                        release_name=self._status.current_release.release_name,
                        current_archive=self._status.current_release.current_archive,
                        archive_progress=self._status.current_release.archive_progress,
                        archive_total=self._status.current_release.archive_total,
                        status=self._status.current_release.status,
                        message=self._status.current_release.message,
                        error=self._status.current_release.error,
                    )
                    if self._status.current_release
                    else None
                ),
                recent_logs=self._status.recent_logs.copy(),
                start_time=self._status.start_time,
                last_completion_time=self._status.last_completion_time,
            )
            return status

    def reset(self) -> None:
        """Reset all status counters."""
        with self._lock:
            self._status = GlobalStatus()
            self._status.last_update = datetime.now()


# Global status tracker instance
_status_tracker = StatusTracker()


def get_status_tracker() -> StatusTracker:
    """Get the global status tracker instance."""
    return _status_tracker


__all__ = ["StatusTracker", "ProcessingStatus", "GlobalStatus", "get_status_tracker"]

