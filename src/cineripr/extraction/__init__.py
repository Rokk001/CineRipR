"""Archive detection and extraction functionality."""

from __future__ import annotations

from .archive_constants import (
    SUPPORTED_ARCHIVE_SUFFIXES,
    TV_TAG_RE,
)
from .archive_detection import (
    ArchiveGroup,
    detect_archives,
    group_related_archives,
    is_archive,
    validate_archive_group,
)
from .archive_extraction import (
    extract_archive,
    get_rar_volume_count,
    resolve_seven_zip_command,
)

__all__ = [
    # Constants
    "SUPPORTED_ARCHIVE_SUFFIXES",
    "TV_TAG_RE",
    # Detection
    "ArchiveGroup",
    "detect_archives",
    "group_related_archives",
    "is_archive",
    "validate_archive_group",
    # Extraction
    "extract_archive",
    "get_rar_volume_count",
    "resolve_seven_zip_command",
]

