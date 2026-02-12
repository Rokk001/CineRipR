"""Archive discovery, validation and grouping."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .archive_constants import (
    SUPPORTED_ARCHIVE_SUFFIXES,
    PART_VOLUME_RE,
    R_VOLUME_RE,
    SPLIT_EXT_RE,
)


@dataclass(frozen=True)
class ArchiveGroup:
    """Represents a collection of files belonging to the same archive.

    Attributes:
        key: Unique identifier for this archive group
        primary: Primary/first archive file
        members: All archive parts in order
        order_map: Maps each file to its part index
    """

    key: str
    primary: Path
    members: tuple[Path, ...]
    order_map: dict[Path, int]

    @property
    def part_count(self) -> int:
        """Number of archive parts in this group."""
        return len(self.members)


def is_supported_archive(entry: Path) -> bool:
    """Check if a file is a supported archive format.

    Supports:
    - RAR archives (including multi-part: .rar, .r00, .r01, etc.)
    - ZIP archives (including split: .zip, .z01, .z02, etc.)
    - TAR archives and compressed variants (.tar.gz, .tar.bz2, etc.)
    - Multi-part archives (.part01, .part02, etc.)
    - DCTMP files (temporary archive files)
    """
    name = entry.name.lower()

    # Direct format match
    if name.endswith(".rar"):
        return True
    if name.endswith(".dctmp"):
        return True
    if any(name.endswith(suffix) for suffix in SUPPORTED_ARCHIVE_SUFFIXES):
        return True

    # Multi-part archive patterns
    part_match = PART_VOLUME_RE.match(name)
    if part_match:
        candidate = f"{part_match.group('base')}{part_match.group('ext')}"
        if any(
            candidate.endswith(suffix) for suffix in SUPPORTED_ARCHIVE_SUFFIXES
        ) or candidate.endswith(".rar"):
            return True

    # RAR volume pattern (.r00, .r01, etc.)
    if R_VOLUME_RE.match(name):
        return True

    # Split archive pattern (.001, .002, etc.)
    split_match = SPLIT_EXT_RE.match(name)
    if split_match:
        candidate = f"{split_match.group('base')}{split_match.group('ext')}"
        if any(
            candidate.endswith(suffix) for suffix in SUPPORTED_ARCHIVE_SUFFIXES
        ) or candidate.endswith(".rar"):
            return True

    return False


def split_directory_entries(directory: Path) -> tuple[list[Path], list[Path]]:
    """Split directory contents into supported archives and other files.

    Returns:
        Tuple of (supported_archives, unsupported_files)
    """
    supported: list[Path] = []
    unsupported: list[Path] = []

    for entry in sorted(directory.iterdir(), key=lambda path: path.name.lower()):
        if not entry.is_file():
            continue
        if is_supported_archive(entry):
            supported.append(entry)
        else:
            unsupported.append(entry)

    return supported, unsupported


def compute_archive_group_key(archive: Path) -> tuple[str, int]:
    """Compute grouping key and order index for an archive file.

    Returns:
        Tuple of (group_key, part_index)
        - group_key: Identifier shared by all parts of the same archive
        - part_index: Order index for this part (-1 for single-part archives)
    """
    lower_name = archive.name.lower()
    
    # Strip .dctmp extension if present to group with main archive
    if lower_name.endswith(".dctmp"):
        lower_name = lower_name[:-6]  # remove .dctmp

    # Multi-part pattern: file.part01.rar (CHECK THIS FIRST!)
    part_match = PART_VOLUME_RE.match(lower_name)
    if part_match:
        base = f"{part_match.group('base')}{part_match.group('ext')}"
        part_index = int(part_match.group("index") or 0)
        return base, max(part_index, 0)

    # RAR volume pattern: file.r00, file.r01
    r_match = R_VOLUME_RE.match(lower_name)
    if r_match:
        base = f"{r_match.group('base')}.rar"
        part_index = int(r_match.group("index") or 0)
        return base, max(part_index, 0)

    # Split pattern: file.zip.001, file.zip.002
    split_match = SPLIT_EXT_RE.match(lower_name)
    if split_match:
        base = f"{split_match.group('base')}{split_match.group('ext')}"
        part_index = int(split_match.group("index") or 0)
        return base, max(part_index, 0)

    # Single RAR file (only if no other pattern matched)
    if lower_name.endswith(".rar"):
        return lower_name, -1

    # Unknown pattern - treat as single file
    return lower_name, -1


def build_archive_groups(archives: Sequence[Path]) -> list[ArchiveGroup]:
    """Group related archive files together (multi-part archives).

    Args:
        archives: List of archive files to group

    Returns:
        List of ArchiveGroup objects, one per logical archive
    """
    grouped: dict[str, list[tuple[int, Path]]] = {}

    for archive in archives:
        key, order = compute_archive_group_key(archive)
        grouped.setdefault(key, []).append((order, archive))

    groups: list[ArchiveGroup] = []
    for key, items in grouped.items():
        # Sort by part index, then by filename
        items.sort(key=lambda item: (item[0], item[1].name.lower()))
        ordered_paths = tuple(path for _order, path in items)
        order_map = {path: order for order, path in items}
        primary = ordered_paths[0]

        groups.append(
            ArchiveGroup(
                key=key,
                primary=primary,
                members=ordered_paths,
                order_map=order_map,
            )
        )

    # Sort groups by primary filename
    groups.sort(key=lambda group: group.primary.name.lower())
    return groups


def validate_archive_group(
    group: ArchiveGroup, *, check_completeness: bool = True
) -> tuple[bool, str | None]:
    """Validate that an archive group is complete and ready for extraction.

    Args:
        group: Archive group to validate
        check_completeness: If True, check if all parts are present (for multi-part archives)

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if group can be extracted
        - error_message: Description of problem if invalid, None if valid
    """
    # Check for .dctmp files in the group - this indicates incomplete download
    for member in group.members:
        if member.name.lower().endswith(".dctmp"):
            return False, f"part {member.name} is still downloading (.dctmp)"

    orders = group.order_map
    positives = sorted(order for order in orders.values() if order >= 0)

    if positives:
        # Determine start index (0-based or 1-based)
        start = 0 if 0 in positives else 1 if 1 in positives else positives[0]
        expected = list(range(start, start + len(positives)))

        # Check for missing parts in the sequence
        if positives != expected:
            missing = sorted(set(expected) - set(positives))
            if missing:
                return False, "missing volume index(es): " + ", ".join(
                    str(value) for value in missing
                )

        # For multi-part archives, check if all parts are present
        # This prevents extraction when download is still in progress
        if check_completeness and len(positives) > 0:
            # Check if there are any files with higher indices that might be part of this archive
            # This indicates the download is still in progress
            last_index = max(positives)
            last_part = next(
                (
                    member
                    for member, idx in group.order_map.items()
                    if idx == last_index
                ),
                None,
            )
            if last_part and last_part.exists():
                parent_dir = last_part.parent
                try:
                    # Check for potential next parts in the same directory
                    for entry in parent_dir.iterdir():
                        if not entry.is_file() or entry in group.members:
                            continue
                        entry_lower = entry.name.lower()
                        # Check if this might be a next part of the same archive
                        part_match = PART_VOLUME_RE.match(entry_lower)
                        if part_match:
                            part_idx = int(part_match.group("index") or 0)
                            candidate_base = (
                                f"{part_match.group('base')}{part_match.group('ext')}"
                            )
                            if (
                                candidate_base == group.key.lower()
                                and part_idx > last_index
                            ):
                                return (
                                    False,
                                    f"found part {part_idx} but sequence ends at {last_index} - download may still be in progress",
                                )
                        # Check RAR volume pattern
                        r_match = R_VOLUME_RE.match(entry_lower)
                        if r_match:
                            part_idx = int(r_match.group("index") or 0)
                            candidate_base = f"{r_match.group('base')}.rar"
                            if (
                                candidate_base == group.key.lower()
                                and part_idx > last_index
                            ):
                                return (
                                    False,
                                    f"found volume {part_idx} but sequence ends at {last_index} - download may still be in progress",
                                )
                        # Check split pattern
                        split_match = SPLIT_EXT_RE.match(entry_lower)
                        if split_match:
                            part_idx = int(split_match.group("index") or 0)
                            candidate_base = (
                                f"{split_match.group('base')}{split_match.group('ext')}"
                            )
                            if (
                                candidate_base == group.key.lower()
                                and part_idx > last_index
                            ):
                                return (
                                    False,
                                    f"found part {part_idx} but sequence ends at {last_index} - download may still be in progress",
                                )
                except OSError:
                    # If we can't check the directory, assume it's OK
                    pass

        # Old RAR volume format (.r00, .r01) needs base .rar file
        # But modern .partXX.rar format does NOT need a base .rar file
        if group.key.endswith(".rar") and not any(
            order < 0 for order in orders.values()
        ):
            # Check if this is old-style .rXX volumes (not modern .partXX.rar)
            # Modern .partXX.rar files contain "part" in the filename
            is_modern_part_format = any(
                ".part" in member.name.lower() for member in group.members
            )
            # Only require base .rar file for old-style .rXX volumes
            if not is_modern_part_format:
                return False, "missing base .rar volume"

    # Check primary file exists
    if not group.primary.exists():
        return False, "primary archive file is missing"

    return True, None


__all__ = [
    "ArchiveGroup",
    "is_supported_archive",
    "split_directory_entries",
    "build_archive_groups",
    "validate_archive_group",
]
