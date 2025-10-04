"""Progress bar helpers."""

from __future__ import annotations


def format_progress(current: int, total: int, *, width: int = 20) -> str:
    if total <= 0:
        return f"[{'-' * width}] 0% (0/0)"
    ratio = max(0.0, min(1.0, current / total))
    filled = int(ratio * width)
    if current > 0 and filled == 0:
        filled = 1
    bar = "#" * filled + "-" * (width - filled)
    percent = int(round(ratio * 100))
    return f"[{bar}] {percent:3d}% ({current}/{total})"


__all__ = ["format_progress"]
