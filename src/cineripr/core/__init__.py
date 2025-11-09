"""Core business logic for CineRipR archive processing."""

from __future__ import annotations

from .archives import ProcessResult, process_downloads
from .cleanup import cleanup_finished
from .file_operations import (
    chmod_recursive,
    copy_file_with_metadata,
    delete_empty_directories,
    move_directory_contents,
)
from .path_utils import (
    build_tv_show_path,
    detect_show_and_season,
    is_tv_show_release,
)

__all__ = [
    # Main processing
    "process_downloads",
    "ProcessResult",
    # Cleanup
    "cleanup_finished",
    # File operations
    "chmod_recursive",
    "copy_file_with_metadata",
    "delete_empty_directories",
    "move_directory_contents",
    # Path utilities
    "build_tv_show_path",
    "detect_show_and_season",
    "is_tv_show_release",
]

