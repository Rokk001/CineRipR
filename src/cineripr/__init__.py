"""CineRipR compatibility package.

This package forwards to the existing implementation in `emby_extractor` to
avoid breaking existing imports while the internal refactor is phased.
"""

from __future__ import annotations

from emby_extractor import __version__  # re-export

__all__ = ["__version__"]


