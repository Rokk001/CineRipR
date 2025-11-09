"""Archive detection and extraction functionality."""

from __future__ import annotations

from .archive_constants import (
    ARCHIVE_EXTENSIONS,
    RAR_EXTENSIONS,
    ZIP_EXTENSIONS,
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
    "ARCHIVE_EXTENSIONS",
    "RAR_EXTENSIONS",
    "ZIP_EXTENSIONS",
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

