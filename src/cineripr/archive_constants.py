"""Constants and regular expressions for archive processing."""

from __future__ import annotations

import re
import shutil


def _build_supported_suffixes() -> tuple[str, ...]:
    """Build list of supported archive suffixes from shutil."""
    suffixes: set[str] = set()
    for _name, suffix_list, _description in shutil.get_unpack_formats():
        for suffix in suffix_list:
            suffixes.add(suffix.lower())
    return tuple(sorted(suffixes, key=len, reverse=True))


# Archive format support
SUPPORTED_ARCHIVE_SUFFIXES: tuple[str, ...] = _build_supported_suffixes()
UNWANTED_EXTRACTED_SUFFIXES = {".sfv"}

# Category names
TV_CATEGORY = "TV-Shows"
MOVIES_CATEGORY = "Movies"

# Normalized subfolder names
SUBFOLDER_SUBS = "Subs"
SUBFOLDER_SAMPLE = "Sample"
SUBFOLDER_OTHER = "Sonstige"

# Regular expressions for pattern matching
TV_TAG_RE = re.compile(r"s\d{2}(?:e\d{2})?", re.IGNORECASE)
# Some releases contain only episode tags like E01/E001 without an Sxx season tag
EPISODE_ONLY_TAG_RE = re.compile(r"(?<![a-z])e\d{2,3}(?![a-z])", re.IGNORECASE)
SEASON_DIR_RE = re.compile(r"^season\s*(\d+)$", re.IGNORECASE)
# Short season folder variant: "S03"
SEASON_SHORT_DIR_RE = re.compile(r"^s\d{1,2}$", re.IGNORECASE)
# German variant: "Staffel 1", "Staffel 01"
STAFFEL_DIR_RE = re.compile(r"^staffel\s*(\d+)$", re.IGNORECASE)
SEASON_TAG_RE = re.compile(r"\.S(\d+)", re.IGNORECASE)
SEASON_TAG_ALT_RE = re.compile(r"S(\d+)", re.IGNORECASE)

# Multi-part archive patterns
PART_VOLUME_RE = re.compile(
    r"^(?P<base>.+?)\.part(?P<index>\d+)(?P<ext>(?:\.[^.]+)+)$", re.IGNORECASE
)
R_VOLUME_RE = re.compile(r"^(?P<base>.+?)\.r(?P<index>\d+)$", re.IGNORECASE)
SPLIT_EXT_RE = re.compile(
    r"^(?P<base>.+?)(?P<ext>(?:\.[^.]+)+)\.(?P<index>\d+)$", re.IGNORECASE
)


__all__ = [
    "SUPPORTED_ARCHIVE_SUFFIXES",
    "UNWANTED_EXTRACTED_SUFFIXES",
    "TV_CATEGORY",
    "MOVIES_CATEGORY",
    "SUBFOLDER_SUBS",
    "SUBFOLDER_SAMPLE",
    "SUBFOLDER_OTHER",
    "TV_TAG_RE",
    "EPISODE_ONLY_TAG_RE",
    "SEASON_DIR_RE",
    "SEASON_TAG_RE",
    "SEASON_TAG_ALT_RE",
    "PART_VOLUME_RE",
    "R_VOLUME_RE",
    "SPLIT_EXT_RE",
    "STAFFEL_DIR_RE",
]
