"""Path utilities for TV show organization and directory management."""

from __future__ import annotations

import re
from pathlib import Path
import os

from ..extraction.archive_constants import (
    TV_CATEGORY,
    MOVIES_CATEGORY,
    TV_TAG_RE,
    EPISODE_ONLY_TAG_RE,
    SEASON_DIR_RE,
    SEASON_SHORT_DIR_RE,
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
        SEASON_DIR_RE.match(name) is not None
        or STAFFEL_DIR_RE.match(name) is not None
        or SEASON_SHORT_DIR_RE.match(name) is not None
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

    # Find the first path segment that carries a season tag (e.g., Show.S02...)
    tagged_part: str | None = None
    for segment in parts:
        if SEASON_TAG_RE.search(segment) or SEASON_TAG_ALT_RE.search(segment):
            tagged_part = segment
            break

    if tagged_part is not None:
        season_match = SEASON_TAG_RE.search(tagged_part) or SEASON_TAG_ALT_RE.search(
            tagged_part
        )
        if season_match:
            season_num = int(season_match.group(1))
            season_normalized = f"Season {season_num:02d}"

            # If the tagged_part is a pure season directory (e.g., 'S01', 'Season 01', 'Staffel 01'),
            # derive the show name from the first rel_path component (parts[0]).
            pure_season_dir = (
                SEASON_SHORT_DIR_RE.match(tagged_part) is not None
                or SEASON_DIR_RE.match(tagged_part) is not None
                or STAFFEL_DIR_RE.match(tagged_part) is not None
            )
            if pure_season_dir:
                show_name = parts[0].replace(".", " ").strip()
            else:
                # Extract show name from the tagged segment by stripping everything from .Sxx
                show_name = re.sub(r"\.S\d+.*", "", tagged_part, flags=re.IGNORECASE)
                show_name = show_name.replace(".", " ").strip()
                if not show_name and parts:
                    # Fallback to the first component if we somehow stripped everything
                    show_name = parts[0].replace(".", " ").strip()

            return base_prefix / show_name / season_normalized

    # If no season tag anywhere, but an episode-only tag exists in any segment,
    # treat it as a no-season show and place files directly under the show name.
    for segment in parts:
        match = EPISODE_ONLY_TAG_RE.search(segment)
        if match:
            # Use only the portion before the episode tag as the show name
            prefix = segment[: match.start()]
            show_name = prefix.replace(".", " ").strip().strip("-")
            if not show_name:
                show_name = parts[0].replace(".", " ").strip()
            return base_prefix / show_name

    # No season/episode information found; mirror relative path
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

    # Shallow scan immediate children first
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

    # Recursive scan (limited depth) to robustly classify nested structures
    max_depth = 3
    try:
        root_parts = len(root.parts)
        for dirpath, dirnames, filenames in os.walk(root):
            depth = len(Path(dirpath).parts) - root_parts
            if depth > max_depth:
                # Prune deep traversal
                dirnames[:] = []
                continue
            # Season folders anywhere below
            for d in dirnames:
                if (
                    is_season_directory(Path(d))
                    or TV_TAG_RE.search(d)
                    or EPISODE_ONLY_TAG_RE.search(d)
                ):
                    return True
            # Files with TV tags anywhere below
            for f in filenames:
                if TV_TAG_RE.search(f) or EPISODE_ONLY_TAG_RE.search(f):
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
