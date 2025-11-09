"""Core business logic for CineRipR archive processing."""

from __future__ import annotations

from .archives import ProcessResult, process_downloads
from .cleanup import cleanup_finished
from .path_utils import (
    build_tv_show_path,
)

__all__ = [
    # Main processing
    "process_downloads",
    "ProcessResult",
    # Cleanup
    "cleanup_finished",
    # Path utilities
    "build_tv_show_path",
]

