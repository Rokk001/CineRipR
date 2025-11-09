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
                conn.commit()
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

