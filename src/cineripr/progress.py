"""Progress presentation utilities."""

from __future__ import annotations

import os
import random
import shutil
import sys

# Windows Console API setup
_WINDOWS_CONSOLE = None
_CTYPES_AVAILABLE = False

if sys.platform == "win32":
    try:
        import ctypes

        _CTYPES_AVAILABLE = True

        kernel32 = ctypes.windll.kernel32
        # Get stdout handle
        stdout_handle = kernel32.GetStdHandle(-11)
        # Enable virtual terminal processing
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(stdout_handle, ctypes.byref(mode))
        mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        kernel32.SetConsoleMode(stdout_handle, mode)

        # Store for direct cursor control
        _WINDOWS_CONSOLE = {
            "kernel32": kernel32,
            "handle": stdout_handle,
        }
    except Exception:
        pass  # Silently fail if we can't enable it

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


def _get_terminal_width() -> int:
    """Get the current terminal width, with fallback to 100."""
    try:
        size = shutil.get_terminal_size(fallback=(100, 24))
        return size.columns
    except Exception:
        return 100


def _truncate_to_fit(text: str, max_width: int | None = None) -> str:
    """Truncate text to fit terminal width.

    Args:
        text: Text to truncate
        max_width: Maximum width (defaults to terminal width)

    Returns:
        Truncated text with '...' if too long
    """
    if max_width is None:
        max_width = _get_terminal_width()

    # Account for ANSI color codes which don't take visual space
    # Simple approach: if text contains ANSI codes, be more generous with limit
    if "\033[" in text:
        # Add some buffer for color codes (rough estimate)
        effective_length = len(text) - text.count("\033[") * 8
    else:
        effective_length = len(text)

    if effective_length > max_width:
        # Find where to cut (accounting for '...')
        cut_at = max_width - 3
        # Try to cut at a word boundary if possible
        if cut_at > 20:  # Only if we have reasonable space
            last_space = text[:cut_at].rfind(" ")
            if last_space > cut_at - 20:  # Don't cut too early
                cut_at = last_space
        return text[:cut_at] + "..."
    return text


def _pick_color(previous: str | None) -> str:
    choices = list(_PALETTE)
    if previous in choices and len(choices) > 1:
        choices.remove(previous)
    return random.choice(choices)


def next_progress_color() -> str:
    """Return the next progress color, updating the shared last-color state.

    Ensures the new color differs from the previously used one when possible.
    """
    prev = getattr(ProgressTracker, "_last_color", None)
    chosen = _pick_color(prev)
    setattr(ProgressTracker, "_last_color", chosen)
    return chosen


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
        indent: int = 0,
        prefix: str = "",
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
        self._inline = bool(single_line)
        self._last_len = 0
        self._indent = max(0, int(indent))
        self._prefix = prefix

    def _emit(self, logger, message: str) -> None:
        indent_spaces = " " * self._indent
        tree = self._prefix if self._prefix else ""
        text = f"{indent_spaces}{tree}{format_progress(self.current, self.total, width=self.width, color=self.color)} {message}"

        # Always truncate to fit terminal width
        text = _truncate_to_fit(text)

        if self._inline:
            # For inline mode, bypass logger completely and use direct stderr
            # stderr is not affected by logging configuration
            try:
                # Clear the line and write new content to stderr
                sys.stderr.write(f"\r{' ' * self._last_len}\r")  # Clear previous line
                sys.stderr.write(text)
                sys.stderr.flush()
                self._last_len = len(text)
            except (OSError, Exception):
                # If stderr fails, disable inline mode and use regular logging
                self._inline = False
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
        # If we were updating inline, add a newline to move to next line
        if self._inline:
            sys.stderr.write("\n")
            sys.stderr.flush()
            self._last_len = 0  # Reset for next use


__all__ = [
    "format_progress",
    "ProgressTracker",
    "next_progress_color",
    "truncate_for_terminal",
]


def truncate_for_terminal(text: str) -> str:
    """Public wrapper for truncating text to terminal width.

    Args:
        text: Text to truncate

    Returns:
        Text truncated to fit terminal width
    """
    return _truncate_to_fit(text)
