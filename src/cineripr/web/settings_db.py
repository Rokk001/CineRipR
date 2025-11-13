"""Settings persistence using SQLite."""

import json
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any

DEFAULT_SETTINGS = {
    # Retention
    "finished_retention_days": 15,
    "enable_delete": False,
    # Scheduling
    "repeat_forever": True,
    "repeat_after_minutes": 30,
    # Subfolders
    "include_sample": False,
    "include_sub": True,
    "include_other": False,
    # Performance
    "parallel_extractions": 1,
    "cpu_cores_per_extraction": 2,
    "auto_detect_hardware": True,
    "max_ram_usage_percent": 75,
    "min_free_ram_gb": 4.0,
    "ssd_only_parallel": True,
    # File Processing
    "file_stability_hours": 24,
    # UI
    "theme": "dark",
    "toast_notifications": True,
    "toast_sound": False,
    "auto_clear_notifications_days": 7,
    # Advanced
    "demo_mode": False,
}


class SettingsDB:
    """Thread-safe settings database."""

    def __init__(self, db_path: Path):
        """Initialize settings database."""
        self.db_path = db_path
        self._lock = Lock()
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with self._lock:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                """)
                # Statistics table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        processed_count INTEGER DEFAULT 0,
                        failed_count INTEGER DEFAULT 0,
                        unsupported_count INTEGER DEFAULT 0,
                        deleted_count INTEGER DEFAULT 0,
                        cleanup_failed_count INTEGER DEFAULT 0,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # History table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        release_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        processed_archives INTEGER DEFAULT 0,
                        failed_archives INTEGER DEFAULT 0,
                        duration_seconds REAL DEFAULT 0.0,
                        extracted_files TEXT,
                        error_messages TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        attempt_count INTEGER DEFAULT 1
                    )
                """)
                # File status table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS file_status (
                        file_path TEXT PRIMARY KEY,
                        file_size INTEGER,
                        last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Queue table (NEW in v2.5.1)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS queue (
                        id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        archive_count INTEGER DEFAULT 0,
                        error TEXT,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                
                # MIGRATION: Fix invalid repeat_after_minutes values (v2.4.3)
                # Old versions could have 0, which breaks countdown
                cursor = conn.execute(
                    "SELECT value FROM settings WHERE key = 'repeat_after_minutes'"
                )
                row = cursor.fetchone()
                if row:
                    try:
                        current_value = json.loads(row[0])
                        if isinstance(current_value, (int, float)) and current_value < 1:
                            # Invalid value, fix it
                            conn.execute(
                                "UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = 'repeat_after_minutes'",
                                (json.dumps(30),)
                            )
                            conn.commit()
                            import logging
                            logging.getLogger(__name__).warning(
                                "Migrated repeat_after_minutes from %s to 30 (default)", current_value
                            )
                    except (json.JSONDecodeError, ValueError):
                        pass  # Ignore malformed values
                
                # Migration: Add attempt_count column if it doesn't exist (v2.5.13)
                try:
                    conn.execute("ALTER TABLE history ADD COLUMN attempt_count INTEGER DEFAULT 1")
                    conn.commit()
                except sqlite3.OperationalError:
                    # Column already exists, ignore
                    pass
            finally:
                conn.close()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute(
                    "SELECT value FROM settings WHERE key = ?", (key,)
                )
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return default
            finally:
                conn.close()

    def set(self, key: str, value: Any):
        """Set a setting value."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute(
                    """
                    INSERT INTO settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (key, json.dumps(value)),
                )
                conn.commit()
            finally:
                conn.close()

    def get_all(self) -> dict:
        """Get all settings."""
        settings = DEFAULT_SETTINGS.copy()

        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute("SELECT key, value FROM settings")
                for key, value in cursor.fetchall():
                    settings[key] = json.loads(value)
            finally:
                conn.close()

        return settings

    def set_metadata(self, key: str, value: str):
        """Set metadata value."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute(
                    """
                    INSERT INTO metadata (key, value)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (key, value),
                )
                conn.commit()
            finally:
                conn.close()

    def get_metadata(self, key: str, default: str | None = None) -> str | None:
        """Get metadata value."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute(
                    "SELECT value FROM metadata WHERE key = ?", (key,)
                )
                row = cursor.fetchone()
                return row[0] if row else default
            finally:
                conn.close()

    def is_first_run(self) -> bool:
        """Check if this is the first run."""
        return self.get_metadata("initialized") != "true"

    def mark_initialized(self):
        """Mark database as initialized."""
        self.set_metadata("initialized", "true")

    def save_statistics(self, stats: dict):
        """Save statistics to database."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                # Delete old statistics (keep only latest)
                conn.execute("DELETE FROM statistics")
                
                # Insert new statistics
                conn.execute("""
                    INSERT INTO statistics (
                        processed_count, failed_count, unsupported_count,
                        deleted_count, cleanup_failed_count
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    stats.get("processed_count", 0),
                    stats.get("failed_count", 0),
                    stats.get("unsupported_count", 0),
                    stats.get("deleted_count", 0),
                    stats.get("cleanup_failed_count", 0),
                ))
                conn.commit()
            finally:
                conn.close()

    def load_statistics(self) -> dict:
        """Load statistics from database."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute("""
                    SELECT processed_count, failed_count, unsupported_count,
                           deleted_count, cleanup_failed_count
                    FROM statistics
                    ORDER BY id DESC
                    LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    return {
                        "processed_count": row[0],
                        "failed_count": row[1],
                        "unsupported_count": row[2],
                        "deleted_count": row[3],
                        "cleanup_failed_count": row[4],
                    }
                return {
                    "processed_count": 0,
                    "failed_count": 0,
                    "unsupported_count": 0,
                    "deleted_count": 0,
                    "cleanup_failed_count": 0,
                }
            finally:
                conn.close()

    def save_history(self, history_items: list):
        """Save history items to database."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                # Keep only last 100 items
                conn.execute("""
                    DELETE FROM history 
                    WHERE id NOT IN (
                        SELECT id FROM history ORDER BY id DESC LIMIT 100
                    )
                """)
                
                # Insert new history items
                for item in history_items[-100:]:  # Keep only last 100
                    conn.execute("""
                        INSERT INTO history (
                            release_name, status, processed_archives, failed_archives,
                            duration_seconds, extracted_files, error_messages, timestamp, attempt_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item.get("release_name", ""),
                        item.get("status", "completed"),
                        item.get("processed_archives", 0),
                        item.get("failed_archives", 0),
                        item.get("duration_seconds", 0.0),
                        json.dumps(item.get("extracted_files", [])),
                        json.dumps(item.get("error_messages", [])),
                        item.get("timestamp", ""),
                        item.get("attempt_count", 1),  # NEW
                    ))
                conn.commit()
            finally:
                conn.close()

    def load_history(self) -> list:
        """Load history from database."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute("""
                    SELECT release_name, status, processed_archives, failed_archives,
                           duration_seconds, extracted_files, error_messages, timestamp, attempt_count
                    FROM history
                    ORDER BY id DESC
                    LIMIT 100
                """)
                history = []
                for row in cursor.fetchall():
                    history.append({
                        "release_name": row[0],
                        "status": row[1],
                        "processed_archives": row[2],
                        "failed_archives": row[3],
                        "duration_seconds": row[4],
                        "extracted_files": json.loads(row[5]) if row[5] else [],
                        "error_messages": json.loads(row[6]) if row[6] else [],
                        "timestamp": row[7],
                        "attempt_count": row[8] if len(row) > 8 else 1,  # NEW: Default to 1 if column doesn't exist
                    })
                return history
            finally:
                conn.close()

    def save_file_status(self, file_path: str, file_size: int):
        """Save file status for comparison on next run."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute("""
                    INSERT INTO file_status (file_path, file_size, last_check)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(file_path) DO UPDATE SET
                        file_size = excluded.file_size,
                        last_check = CURRENT_TIMESTAMP
                """, (file_path, file_size))
                conn.commit()
            finally:
                conn.close()

    def get_file_status(self, file_path: str) -> tuple[int, float] | None:
        """Get previous file status."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute("""
                    SELECT file_size, last_check
                    FROM file_status
                    WHERE file_path = ?
                """, (file_path,))
                row = cursor.fetchone()
                if row:
                    # Parse timestamp
                    import time
                    from datetime import datetime
                    last_check_str = row[1]
                    try:
                        last_check = datetime.fromisoformat(last_check_str.replace("Z", "+00:00")).timestamp()
                    except (ValueError, AttributeError):
                        last_check = time.time()
                    return (row[0], last_check)
                return None
            finally:
                conn.close()

    def cleanup_old_file_status(self, days: int = 7):
        """Remove file status entries older than specified days."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute("""
                    DELETE FROM file_status
                    WHERE last_check < datetime('now', '-' || ? || ' days')
                """, (days,))
                conn.commit()
            finally:
                conn.close()

    def save_queue(self, queue_items: list[dict]):
        """Save queue to database (NEW in v2.5.1)."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                # Clear existing queue
                conn.execute("DELETE FROM queue")
                
                # Insert all queue items
                for item in queue_items:
                    conn.execute("""
                        INSERT INTO queue (id, status, archive_count, error, added_at, updated_at)
                        VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                    """, (item['id'], item['status'], item.get('archive_count', 0), item.get('error')))
                
                conn.commit()
            finally:
                conn.close()

    def load_queue(self) -> list[dict]:
        """Load queue from database (NEW in v2.5.1)."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute("""
                    SELECT id, status, archive_count, error, added_at, updated_at
                    FROM queue
                    ORDER BY added_at ASC
                """)
                
                queue_items = []
                for row in cursor.fetchall():
                    queue_items.append({
                        'id': row[0],
                        'status': row[1],
                        'archive_count': row[2],
                        'error': row[3] if row[3] else None,
                    })
                return queue_items
            finally:
                conn.close()


# Global instance
_settings_db: SettingsDB | None = None
_db_lock = Lock()


def get_settings_db(db_path: Path | None = None) -> SettingsDB:
    """Get or create settings database instance."""
    global _settings_db

    with _db_lock:
        if _settings_db is None:
            if db_path is None:
                # Try multiple paths in order of preference
                possible_paths = [
                    Path("/config/cineripr_settings.db"),  # Docker volume
                    Path("/data/cineripr_settings.db"),   # Data directory
                    Path("./cineripr_settings.db"),        # Current directory
                    Path("/tmp/cineripr_settings.db"),     # Temp directory
                ]
                
                db_path = None
                for path in possible_paths:
                    try:
                        # Try to create parent directory
                        path.parent.mkdir(parents=True, exist_ok=True)
                        # Try to create a test file to check write permissions
                        test_file = path.parent / ".test_write"
                        test_file.touch()
                        test_file.unlink()
                        db_path = path
                        break
                    except (OSError, PermissionError):
                        continue
                
                # Fallback to current directory if all else fails
                if db_path is None:
                    db_path = Path("./cineripr_settings.db")
                    db_path.parent.mkdir(parents=True, exist_ok=True)
            
            _settings_db = SettingsDB(db_path)

        return _settings_db


__all__ = ["SettingsDB", "get_settings_db", "DEFAULT_SETTINGS"]

