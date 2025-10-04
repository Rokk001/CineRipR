"""Progress presentation utilities."""

from __future__ import annotations

import os
import sys

_BLUE = "\033[34m"
_RESET = "\033[0m"


def _supports_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


_COLOR_ENABLED = _supports_color()


def _paint(text: str) -> str:
    if not _COLOR_ENABLED:
        return text
    return f"{_BLUE}{text}{_RESET}"


def format_progress(current: int, total: int, *, width: int = 20) -> str:
    safe_total = max(total, 1)
    safe_current = max(0, min(current, safe_total))
    ratio = safe_current / safe_total
    filled = int(ratio * width)
    if safe_current > 0 and filled == 0:
        filled = 1
    bar = "#" * filled + "-" * (width - filled)
    percent = int(round(ratio * 100))
    return f"{_paint('[' + bar + ']')} {percent:3d}% ({safe_current}/{safe_total})"


class ProgressTracker:
    """Utility to emit progress log lines with consistent formatting."""

    def __init__(self, total: int, *, width: int = 20) -> None:
        self.total = max(int(total), 1)
        self.width = width
        self.current = 0

    def _emit(self, logger, message: str) -> None:
        logger.info("%s %s", format_progress(self.current, self.total, width=self.width), message)

    def log(self, logger, message: str) -> None:
        self._emit(logger, message)

    def advance(self, logger, message: str, *, steps: int = 1, absolute: int | None = None) -> None:
        if absolute is not None:
            self.current = max(0, min(self.total, absolute))
        else:
            self.current = max(0, min(self.total, self.current + steps))
        self._emit(logger, message)

    def complete(self, logger, message: str) -> None:
        self.current = self.total
        self._emit(logger, message)


__all__ = ["format_progress", "ProgressTracker"]
