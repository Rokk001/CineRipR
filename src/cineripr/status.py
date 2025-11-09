"""Status tracking for WebGUI."""

from __future__ import annotations

import os
import shutil
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class QueueItem:
    """Represents an item in the processing queue."""

    name: str
    path: str
    status: str = "pending"  # pending, processing, completed, failed
    archive_count: int = 0
    added_time: datetime = field(default_factory=datetime.now)
    error: str | None = None


@dataclass
class SystemHealth:
    """System health metrics."""

    disk_downloads_total_gb: float = 0.0
    disk_downloads_used_gb: float = 0.0
    disk_downloads_free_gb: float = 0.0
    disk_downloads_percent: float = 0.0
    disk_extracted_total_gb: float = 0.0
    disk_extracted_used_gb: float = 0.0
    disk_extracted_free_gb: float = 0.0
    disk_extracted_percent: float = 0.0
    disk_finished_total_gb: float = 0.0
    disk_finished_used_gb: float = 0.0
    disk_finished_free_gb: float = 0.0
    disk_finished_percent: float = 0.0
    seven_zip_version: str = "Unknown"


@dataclass
class Notification:
    """Notification message."""

    id: str
    type: str  # success, error, warning, info
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    read: bool = False


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
    queue: list[QueueItem] = field(default_factory=list)
    system_health: SystemHealth = field(default_factory=SystemHealth)
    notifications: list[Notification] = field(default_factory=list)

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
            "queue": [
                {
                    "name": item.name,
                    "path": item.path,
                    "status": item.status,
                    "archive_count": item.archive_count,
                    "added_time": item.added_time.isoformat(),
                    "error": item.error,
                }
                for item in self.queue
            ],
            "system_health": {
                "disk_downloads_total_gb": self.system_health.disk_downloads_total_gb,
                "disk_downloads_used_gb": self.system_health.disk_downloads_used_gb,
                "disk_downloads_free_gb": self.system_health.disk_downloads_free_gb,
                "disk_downloads_percent": self.system_health.disk_downloads_percent,
                "disk_extracted_total_gb": self.system_health.disk_extracted_total_gb,
                "disk_extracted_used_gb": self.system_health.disk_extracted_used_gb,
                "disk_extracted_free_gb": self.system_health.disk_extracted_free_gb,
                "disk_extracted_percent": self.system_health.disk_extracted_percent,
                "disk_finished_total_gb": self.system_health.disk_finished_total_gb,
                "disk_finished_used_gb": self.system_health.disk_finished_used_gb,
                "disk_finished_free_gb": self.system_health.disk_finished_free_gb,
                "disk_finished_percent": self.system_health.disk_finished_percent,
                "seven_zip_version": self.system_health.seven_zip_version,
            },
            "notifications": [
                {
                    "id": notif.id,
                    "type": notif.type,
                    "title": notif.title,
                    "message": notif.message,
                    "timestamp": notif.timestamp.isoformat(),
                    "read": notif.read,
                }
                for notif in self.notifications[-20:]  # Last 20 notifications
            ],
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

    # Queue Management
    def add_to_queue(self, name: str, path: str, archive_count: int = 0) -> None:
        """Add an item to the processing queue."""
        with self._lock:
            self._status.queue.append(
                QueueItem(name=name, path=path, archive_count=archive_count)
            )
            self._status.last_update = datetime.now()

    def update_queue_item(
        self, name: str, status: str, error: str | None = None
    ) -> None:
        """Update a queue item's status."""
        with self._lock:
            for item in self._status.queue:
                if item.name == name:
                    item.status = status
                    item.error = error
                    break
            self._status.last_update = datetime.now()

    def remove_from_queue(self, name: str) -> None:
        """Remove an item from the queue."""
        with self._lock:
            self._status.queue = [
                item for item in self._status.queue if item.name != name
            ]
            self._status.last_update = datetime.now()

    def clear_completed_queue_items(self) -> None:
        """Remove completed and failed items from queue."""
        with self._lock:
            self._status.queue = [
                item
                for item in self._status.queue
                if item.status not in ("completed", "failed")
            ]
            self._status.last_update = datetime.now()

    # System Health
    def update_system_health(
        self,
        downloads_path: Path | None = None,
        extracted_path: Path | None = None,
        finished_path: Path | None = None,
        seven_zip_version: str | None = None,
    ) -> None:
        """Update system health metrics."""
        with self._lock:
            if downloads_path and downloads_path.exists():
                usage = shutil.disk_usage(downloads_path)
                self._status.system_health.disk_downloads_total_gb = (
                    usage.total / (1024**3)
                )
                self._status.system_health.disk_downloads_used_gb = (
                    usage.used / (1024**3)
                )
                self._status.system_health.disk_downloads_free_gb = (
                    usage.free / (1024**3)
                )
                self._status.system_health.disk_downloads_percent = (
                    (usage.used / usage.total) * 100 if usage.total > 0 else 0
                )

            if extracted_path and extracted_path.exists():
                usage = shutil.disk_usage(extracted_path)
                self._status.system_health.disk_extracted_total_gb = (
                    usage.total / (1024**3)
                )
                self._status.system_health.disk_extracted_used_gb = (
                    usage.used / (1024**3)
                )
                self._status.system_health.disk_extracted_free_gb = (
                    usage.free / (1024**3)
                )
                self._status.system_health.disk_extracted_percent = (
                    (usage.used / usage.total) * 100 if usage.total > 0 else 0
                )

            if finished_path and finished_path.exists():
                usage = shutil.disk_usage(finished_path)
                self._status.system_health.disk_finished_total_gb = (
                    usage.total / (1024**3)
                )
                self._status.system_health.disk_finished_used_gb = (
                    usage.used / (1024**3)
                )
                self._status.system_health.disk_finished_free_gb = (
                    usage.free / (1024**3)
                )
                self._status.system_health.disk_finished_percent = (
                    (usage.used / usage.total) * 100 if usage.total > 0 else 0
                )

            if seven_zip_version:
                self._status.system_health.seven_zip_version = seven_zip_version

            self._status.last_update = datetime.now()

    # Notifications
    def add_notification(
        self, notif_type: str, title: str, message: str
    ) -> None:
        """Add a notification."""
        with self._lock:
            notif_id = f"{datetime.now().timestamp()}"
            self._status.notifications.append(
                Notification(
                    id=notif_id, type=notif_type, title=title, message=message
                )
            )
            # Keep only last 50 notifications
            if len(self._status.notifications) > 50:
                self._status.notifications = self._status.notifications[-50:]
            self._status.last_update = datetime.now()

    def mark_notification_read(self, notif_id: str) -> None:
        """Mark a notification as read."""
        with self._lock:
            for notif in self._status.notifications:
                if notif.id == notif_id:
                    notif.read = True
                    break
            self._status.last_update = datetime.now()

    def get_unread_notifications(self) -> list[Notification]:
        """Get all unread notifications."""
        with self._lock:
            return [notif for notif in self._status.notifications if not notif.read]


# Global status tracker instance
_status_tracker = StatusTracker()


def get_status_tracker() -> StatusTracker:
    """Get the global status tracker instance."""
    return _status_tracker


__all__ = [
    "StatusTracker",
    "ProcessingStatus",
    "GlobalStatus",
    "QueueItem",
    "SystemHealth",
    "Notification",
    "get_status_tracker",
]

