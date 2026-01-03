"""Move renamed directories to movie_root or tvshow_root."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

_logger = logging.getLogger(__name__)


def move_to_final_destination(
    directory: Path,
    destination_root: Path,
    *,
    overwrite: bool = True,
    logger: logging.Logger | None = None,
) -> bool:
    """Move a directory to the final destination (movie_root or tvshow_root).

    Args:
        directory: Directory to move
        destination_root: Root directory for movies or TV shows
        overwrite: If True, overwrite existing directory at destination
        logger: Optional logger

    Returns:
        True if move was successful, False otherwise
    """
    if logger is None:
        logger = _logger

    if not directory.exists() or not directory.is_dir():
        logger.warning(
            "Source directory %s does not exist or is not a directory", directory
        )
        return False

    if not destination_root.exists():
        try:
            destination_root.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(
                "Failed to create destination root %s: %s", destination_root, e
            )
            return False

    destination = destination_root / directory.name

    # Handle existing destination
    if destination.exists():
        if overwrite:
            try:
                # Remove existing directory
                if destination.is_dir():
                    shutil.rmtree(destination)
                else:
                    destination.unlink()
                logger.info("Removed existing destination: %s", destination)
            except OSError as e:
                logger.error(
                    "Failed to remove existing destination %s: %s", destination, e
                )
                return False
        else:
            logger.warning(
                "Destination %s already exists and overwrite is disabled", destination
            )
            return False

    # Move directory
    try:
        directory.rename(destination)
        logger.info("Moved directory: %s → %s", directory, destination)
        return True
    except OSError as e:
        logger.error("Failed to move directory %s to %s: %s", directory, destination, e)
        return False


__all__ = ["move_to_final_destination"]
