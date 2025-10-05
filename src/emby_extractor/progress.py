"""Progress presentation utilities."""

from __future__ import annotations

import os
import random
import sys

_BLUE = "\033[34m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_MAGENTA = "\033[35m"
_CYAN = "\033[36m"
_RESET = "\033[0m"

_PALETTE = (_RED, _GREEN, _YELLOW, _BLUE, _MAGENTA, _CYAN)


def _supports_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


_COLOR_ENABLED = _supports_color()


def _pick_color(previous: str | None) -> str:
    choices = list(_PALETTE)
    if previous in choices and len(choices) > 1:
        choices.remove(previous)
    return random.choice(choices)


def _paint(text: str, *, color: str | None = None) -> str:
    if not _COLOR_ENABLED:
        return text
    chosen = color or _BLUE
    return f"{chosen}{text}{_RESET}"


def format_progress(
    current: int, total: int, *, width: int = 20, color: str | None = None
) -> str:
    safe_total = max(total, 1)
    safe_current = max(0, min(current, safe_total))
    ratio = safe_current / safe_total
    filled = int(ratio * width)
    if safe_current > 0 and filled == 0:
        filled = 1
    bar = "#" * filled + "-" * (width - filled)
    percent = int(round(ratio * 100))
    return f"{_paint('[' + bar + ']', color=color)} {percent:3d}% ({safe_current}/{safe_total})"


class ProgressTracker:
    """Utility to emit progress log lines with consistent formatting."""

    def __init__(
        self,
        total: int,
        *,
        width: int = 20,
        color: str | None = None,
        single_line: bool = False,
    ) -> None:
        self.total = max(int(total), 1)
        self.width = width
        self.current = 0
        # choose a color different from the last used by any ProgressTracker
        if color is not None or not _COLOR_ENABLED:
            self.color = color
        else:
            prev = getattr(ProgressTracker, "_last_color", None)
            chosen = _pick_color(prev)
            setattr(ProgressTracker, "_last_color", chosen)
            self.color = chosen
        self._inline = bool(single_line and sys.stdout.isatty())
        self._last_len = 0

    def _emit(self, logger, message: str) -> None:
        text = f"{format_progress(self.current, self.total, width=self.width, color=self.color)} {message}"
        if self._inline:
            try:
                line = "\r" + text
                padding = max(0, self._last_len - len(text))
                if padding:
                    line += " " * padding
                sys.stdout.write(line)
                sys.stdout.flush()
                self._last_len = len(text)
            except OSError:
                logger.info(text)
        else:
            logger.info(text)

    def log(self, logger, message: str) -> None:
        self._emit(logger, message)

    def advance(
        self, logger, message: str, *, steps: int = 1, absolute: int | None = None
    ) -> None:
        if absolute is not None:
            self.current = max(0, min(self.total, absolute))
        else:
            self.current = max(0, min(self.total, self.current + steps))
        self._emit(logger, message)

    def complete(self, logger, message: str) -> None:
        self.current = self.total
        self._emit(logger, message)
        if self._inline:
            try:
                sys.stdout.write("\n")
                sys.stdout.flush()
            except OSError:
                pass


__all__ = ["format_progress", "ProgressTracker"]
