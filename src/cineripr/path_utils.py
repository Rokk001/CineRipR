"""Path utilities for TV show organization and directory management."""

from __future__ import annotations

import re
from pathlib import Path

from .archive_constants import (
    TV_CATEGORY,
    MOVIES_CATEGORY,
    TV_TAG_RE,
    EPISODE_ONLY_TAG_RE,
    SEASON_DIR_RE,
    STAFFEL_DIR_RE,
    SEASON_TAG_RE,
    SEASON_TAG_ALT_RE,
)


def is_season_directory(directory: Path) -> bool:
    """Check if a directory name represents a season folder.

    Examples:
        - "Season 1", "Season 01"
        - "season 2", "SEASON 02"

    Returns:
        True if directory matches season pattern
    """
    name = directory.name
    return (
        SEASON_DIR_RE.match(name) is not None or STAFFEL_DIR_RE.match(name) is not None
    )


def extract_season_from_tag(name: str) -> str | None:
    """Extract season directory name from TV show tag.

    Args:
        name: Directory or file name containing TV tag (e.g., "S01", "S01E01")

    Returns:
        Season directory name (e.g., "Season 01") or None if not found
    """
    match = TV_TAG_RE.search(name)
    if match:
        tag = match.group(0).upper()
        # Extract season number from S01 or S01E01 format
        season_match = re.match(r"S(\d+)", tag)
        if season_match:
            season_num = int(season_match.group(1))
            return f"Season {season_num:02d}"
    return None


def build_tv_show_path(base_dir: Path, download_root: Path, base_prefix: Path) -> Path:
    """Build a normalized TV show path with 'Season XX' format.

    Converts paths like:
        12.Monkeys.S01.German.../12.Monkeys.S01E01...
    To:
        TV-Shows/12 Monkeys/Season 01/

    Flattens episode directories - extracts directly into Season folder.

    Args:
        base_dir: Directory to build path for
        download_root: Root of downloads directory
        base_prefix: Category prefix (TV-Shows or Movies)

    Returns:
        Normalized output path
    """
    rel_path = base_dir.relative_to(download_root)
    parts = list(rel_path.parts)

    if not parts:
        return base_prefix / rel_path

    # Extract show name and season from the first directory part
    # This could be a season pack (Sxx) or an episode-only pack (Exx)
    first_part = parts[0]

    # Try to extract season number from the directory name
    season_match = SEASON_TAG_RE.search(first_part)
    if not season_match:
        # Try without dot prefix
        season_match = SEASON_TAG_ALT_RE.search(first_part)

    if season_match:
        season_num = int(season_match.group(1))
        season_normalized = f"Season {season_num:02d}"

        # Extract show name (everything before .SXX)
        show_name = re.sub(r"\.S\d+.*", "", first_part, flags=re.IGNORECASE)
        show_name = show_name.replace(".", " ").strip()

        # Flatten: extract directly to Season folder
        # TV-Shows/ShowName/Season XX/
        return base_prefix / show_name / season_normalized

    # No explicit season info found. If the name contains only episode tags,
    # treat it as a single-season show and extract directly under the show name
    # (no Season subfolder).
    if EPISODE_ONLY_TAG_RE.search(first_part):
        show_name = EPISODE_ONLY_TAG_RE.sub("", first_part)
        show_name = show_name.replace(".", " ").strip().strip("-")
        if not show_name:
            show_name = first_part.replace(".", " ").strip()
        return base_prefix / show_name

    # No season info found, return as-is
    return base_prefix / rel_path


def normalize_special_subdir(name: str) -> str | None:
    """Normalize special subdirectory names.

    Maps various names to standard names:
    - "sub", "subs", "untertitel" -> "Subs"
    - "sample" -> "Sample"
    - "sonstige", "other", "misc" -> "Sonstige"

    Args:
        name: Directory name to normalize

    Returns:
        Normalized name or None if not a special subdirectory
    """
    lower = name.strip().lower()
    if lower in {"sub", "subs", "untertitel"}:
        return "Subs"
    if lower == "sample":
        return "Sample"
    if lower in {"sonstige", "other", "misc"}:
        return "Sonstige"
    return None


def looks_like_tv_show(root: Path) -> bool:
    """Determine if a directory contains TV show content.

    Checks for:
    - Season directories
    - TV tags in directory/file names (S01, S01E01, etc.)

    Args:
        root: Directory to check

    Returns:
        True if directory appears to contain TV shows
    """
    if is_season_directory(root):
        return True
    if TV_TAG_RE.search(root.name) or EPISODE_ONLY_TAG_RE.search(root.name):
        return True

    try:
        for child in root.iterdir():
            if child.is_dir() and (
                is_season_directory(child)
                or TV_TAG_RE.search(child.name)
                or EPISODE_ONLY_TAG_RE.search(child.name)
            ):
                return True
            if child.is_file() and (
                TV_TAG_RE.search(child.name) or EPISODE_ONLY_TAG_RE.search(child.name)
            ):
                return True
    except OSError:
        pass

    return False


def get_category_prefix(directory: Path) -> Path:
    """Determine the category prefix (TV-Shows or Movies) for a directory.

    Args:
        directory: Directory to categorize

    Returns:
        Path object for TV_CATEGORY or MOVIES_CATEGORY
    """
    return Path(TV_CATEGORY) if looks_like_tv_show(directory) else Path(MOVIES_CATEGORY)


__all__ = [
    "is_season_directory",
    "extract_season_from_tag",
    "build_tv_show_path",
    "normalize_special_subdir",
    "looks_like_tv_show",
    "get_category_prefix",
]
