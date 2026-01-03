"""NFO file parser for extracting movie metadata."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)


class MovieMetadata:
    """Movie metadata extracted from NFO file."""

    def __init__(self) -> None:
        """Initialize empty metadata."""
        self.title: str | None = None
        self.original_title: str | None = None
        self.year: str | None = None
        self.edition: str | None = None
        self.sort_title: str | None = None
        self.genre: list[str] = []
        self.country: list[str] = []
        self.director: str | None = None
        self.rating: str | None = None
        self.imdb_id: str | None = None
        self.tmdb_id: str | None = None
        self.video_codec: str | None = None
        self.audio_codec: str | None = None
        self.resolution: str | None = None
        self.video_source: str | None = None
        self.audio_channels: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary for pattern substitution."""
        return {
            "T": self.title or "",  # Title
            "O": self.original_title or "",  # Original title
            "Y": self.year or "",  # Year
            "6": self.edition or "",  # Edition
            "E": self.sort_title or "",  # Sort title
            "G": self.genre,  # Genre (list)
            "U": self.country,  # Country (list)
            "C": self.director or "",  # Director
            "P": self.rating or "",  # Rating
            "I": self.imdb_id or "",  # IMDb ID
            "H": self.video_codec or "",  # Video codec
            "J": self.audio_codec or "",  # Audio codec
            "R": self.resolution or "",  # Resolution
            "S": self.video_source or "",  # Video source
            "A": self.audio_channels or "",  # Audio channels
        }


def parse_nfo_file(nfo_path: Path) -> tuple[MovieMetadata | None, bool]:
    """Parse an NFO file and extract movie metadata.

    Args:
        nfo_path: Path to the NFO file

    Returns:
        Tuple of (MovieMetadata object with extracted data, is_tv_show: bool)
        Returns (None, False) if parsing fails
    """
    if not nfo_path.exists() or not nfo_path.is_file():
        return (None, False)

    try:
        tree = ET.parse(nfo_path)
        root = tree.getroot()

        # Handle both <movie> and <episodedetails> root elements
        if root.tag not in {"movie", "episodedetails"}:
            _logger.debug(
                "NFO file %s does not contain movie/episodedetails root", nfo_path
            )
            return (None, False)

        is_tv_show = root.tag == "episodedetails"
        metadata = MovieMetadata()

        # Extract basic fields
        metadata.title = _get_text(root, "title")
        metadata.original_title = _get_text(root, "originaltitle")
        year_elem = root.find("year")
        if year_elem is not None and year_elem.text:
            metadata.year = year_elem.text.strip()
        metadata.edition = _get_text(root, "edition")
        metadata.sort_title = _get_text(root, "sorttitle")
        metadata.director = _get_text(root, "director")
        metadata.rating = _get_text(root, "rating/value")
        metadata.video_source = _get_text(root, "videosource")

        # Extract genres (can be multiple)
        for genre_elem in root.findall("genre"):
            if genre_elem.text:
                metadata.genre.append(genre_elem.text.strip())

        # Extract countries (can be multiple)
        for country_elem in root.findall("country"):
            if country_elem.text:
                metadata.country.append(country_elem.text.strip())

        # Extract IDs
        imdb_elem = root.find("id[@type='imdb']")
        if imdb_elem is not None and imdb_elem.text:
            metadata.imdb_id = imdb_elem.text.strip()
        else:
            # Fallback: try uniqueid
            uniqueid_elem = root.find("uniqueid[@type='imdb']")
            if uniqueid_elem is not None and uniqueid_elem.text:
                metadata.imdb_id = uniqueid_elem.text.strip()

        tmdb_elem = root.find("uniqueid[@type='tmdb']")
        if tmdb_elem is not None and tmdb_elem.text:
            metadata.tmdb_id = tmdb_elem.text.strip()

        # Extract video/audio info from fileinfo/streamdetails
        fileinfo = root.find("fileinfo/streamdetails")
        if fileinfo is not None:
            video = fileinfo.find("video")
            if video is not None:
                metadata.video_codec = _get_text(video, "codec")
                width = _get_text(video, "width")
                height = _get_text(video, "height")
                if width and height:
                    metadata.resolution = f"{width}x{height}"

            audio = fileinfo.find("audio")
            if audio is not None:
                metadata.audio_codec = _get_text(audio, "codec")
                channels = _get_text(audio, "channels")
                if channels:
                    metadata.audio_channels = channels

        return (metadata, is_tv_show)

    except ET.ParseError as e:
        _logger.warning("Failed to parse NFO file %s: %s", nfo_path, e)
        return (None, False)
    except Exception as e:
        _logger.warning("Error reading NFO file %s: %s", nfo_path, e)
        return (None, False)


def _get_text(element: ET.Element | None, path: str) -> str | None:
    """Get text content from an XML element by path.

    Args:
        element: Root element to search from
        path: XPath-like path (e.g., "rating/value")

    Returns:
        Text content or None if not found
    """
    if element is None:
        return None

    parts = path.split("/")
    current = element
    for part in parts:
        current = current.find(part)
        if current is None:
            return None

    return current.text.strip() if current.text else None


def find_nfo_file(directory: Path) -> Path | None:
    """Find the first NFO file in a directory.

    Args:
        directory: Directory to search

    Returns:
        Path to NFO file or None if not found
    """
    try:
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == ".nfo":
                return file_path
    except OSError:
        pass

    return None


__all__ = ["MovieMetadata", "parse_nfo_file", "find_nfo_file"]
