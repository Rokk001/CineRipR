"""Progress bar helpers."""

from __future__ import annotations

import os
import sys

_BLUE = "[34m"
_RESET = "[0m"


def _supports_color() -> bool:
    return sys.stdout.isatty() and os.environ.get('NO_COLOR') is None


_COLOR_ENABLED = _supports_color()


def _paint_blue(text: str) -> str:
    if not _COLOR_ENABLED:
        return text
    return f"{_BLUE}{text}{_RESET}"


def format_progress(current: int, total: int, *, width: int = 20) -> str:
    if total <= 0:
        bar = '-' * width
        return f"{_paint_blue('[' + bar + ']')} 0% (0/0)"
    ratio = max(0.0, min(1.0, current / total))
    filled = int(ratio * width)
    if current > 0 and filled == 0:
        filled = 1
    bar = '#' * filled + '-' * (width - filled)
    percent = int(round(ratio * 100))
    return f"{_paint_blue('[' + bar + ']')} {percent:3d}% ({current}/{total})"


__all__ = ["format_progress"]
