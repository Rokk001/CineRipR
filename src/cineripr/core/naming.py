"""File and folder naming based on NFO metadata and patterns."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from .nfo_parser import MovieMetadata

_logger = logging.getLogger(__name__)


class PatternInterpreter:
    """Interprets naming patterns and substitutes variables with metadata."""

    def __init__(self, metadata: MovieMetadata) -> None:
        """Initialize with movie metadata.

        Args:
            metadata: Movie metadata from NFO file
        """
        self.metadata = metadata
        self.vars = metadata.to_dict()

    def interpret_folder_pattern(self, pattern: str) -> str:
        """Interpret folder naming pattern.

        Supports patterns like:
        - $T{ ($6)}{ ($Y)} → "Matrix Resurrections (2021)"
        - $D → Directory name

        Args:
            pattern: Pattern string with variables

        Returns:
            Interpreted folder name
        """
        if not pattern or pattern.strip() == "$D":
            # Return directory name (not used in our case, but supported)
            return ""

        result = pattern

        # Handle optional blocks: { ... }
        # Process from innermost to outermost
        while "{" in result and "}" in result:
            result = self._process_optional_blocks(result)

        # Replace all variables
        result = self._replace_variables(result)

        # Clean up: remove multiple spaces, trim
        result = re.sub(r"\s+", " ", result).strip()

        # Remove invalid filename characters
        result = self._sanitize_filename(result)

        return result

    def interpret_file_pattern(self, pattern: str, original_filename: str) -> str:
        """Interpret file naming pattern.

        Supports patterns like:
        - ST → "Matrix Resurrections" (interpreted as $T)
        - $T → Title
        - $T ($Y) → "Matrix Resurrections (2021)"

        Args:
            pattern: Pattern string with variables
            original_filename: Original filename (for extension preservation)

        Returns:
            Interpreted filename (without extension)
        """
        if not pattern:
            # Fallback to original filename without extension
            return Path(original_filename).stem

        result = pattern

        # Special case: "ST" means "Sort Title" or just "Title" ($T)
        if result.strip() == "ST":
            result = "$T"

        # Handle optional blocks
        while "{" in result and "}" in result:
            result = self._process_optional_blocks(result)

        # Replace all variables
        result = self._replace_variables(result)

        # Clean up
        result = re.sub(r"\s+", " ", result).strip()
        result = self._sanitize_filename(result)

        return result

    def _process_optional_blocks(self, text: str) -> str:
        """Process optional blocks { ... } in pattern.

        Optional blocks are only included if they contain at least one non-empty variable.

        Args:
            text: Text with optional blocks

        Returns:
            Text with optional blocks processed
        """
        # Find innermost optional block
        pattern = r"\{([^{}]*)\}"
        match = re.search(pattern, text)

        if not match:
            return text

        block_content = match.group(1)
        block_start = match.start()
        block_end = match.end()

        # Check if block should be included (has non-empty content)
        # Create a temporary result to check if block has content
        temp_result = self._replace_variables(block_content)
        has_content = bool(temp_result.strip())

        if has_content:
            # Include the block (remove braces)
            replacement = block_content
        else:
            # Exclude the block (remove entire block)
            replacement = ""

        # Replace the block in text
        new_text = text[:block_start] + replacement + text[block_end:]
        return new_text

    def _replace_variables(self, text: str) -> str:
        """Replace all variables in text with their values.

        Supports:
        - $T → Title
        - $Y → Year
        - $6 → Edition
        - $G → Genre (comma-separated)
        - $U → Country (comma-separated)
        - And many more...

        Args:
            text: Text with variables

        Returns:
            Text with variables replaced
        """
        result = text

        # Replace simple variables ($T, $Y, etc.)
        for var, value in self.vars.items():
            if isinstance(value, list):
                # Join list with comma and space
                value_str = ", ".join(value) if value else ""
            else:
                value_str = str(value) if value else ""

            # Replace $VAR (exact match, not part of longer variable)
            result = re.sub(rf"\${var}(?![a-zA-Z0-9])", value_str, result)

        # Handle special cases
        # $1 = First letter of title
        if "$1" in result:
            first_letter = self.vars["T"][0] if self.vars["T"] else ""
            result = result.replace("$1", first_letter)

        # $F = Filename (not applicable in our context, but supported)
        if "$F" in result:
            result = result.replace("$F", "")

        # $B = Source folder (not applicable)
        if "$B" in result:
            result = result.replace("$B", "")

        # $D = Directory (not applicable in our context)
        if "$D" in result:
            result = result.replace("$D", "")

        # Handle genre/country separators: $G, $G. $G, $G-
        # Default is comma, but can be changed by following character
        if "$G" in result:
            genre_str = ", ".join(self.vars["G"]) if self.vars["G"] else ""
            # Check for separator after $G
            match = re.search(r"\$G([\s.,-])", result)
            if match:
                separator = match.group(1)
                genre_str = separator.join(self.vars["G"]) if self.vars["G"] else ""
                result = re.sub(r"\$G[\s.,-]", genre_str + match.group(1), result)
            else:
                result = result.replace("$G", genre_str)

        if "$U" in result:
            country_str = ", ".join(self.vars["U"]) if self.vars["U"] else ""
            # Check for separator after $U
            match = re.search(r"\$U([\s.,-])", result)
            if match:
                separator = match.group(1)
                country_str = separator.join(self.vars["U"]) if self.vars["U"] else ""
                result = re.sub(r"\$U[\s.,-]", country_str + match.group(1), result)
            else:
                result = result.replace("$U", country_str)

        return result

    def _sanitize_filename(self, name: str) -> str:
        """Remove invalid filename characters.

        Args:
            name: Filename to sanitize

        Returns:
            Sanitized filename
        """
        # Remove invalid characters for Windows/Linux
        invalid_chars = r'[<>:"/\\|?*]'
        name = re.sub(invalid_chars, "", name)

        # Remove leading/trailing dots and spaces
        name = name.strip(". ")

        # Remove multiple consecutive spaces
        name = re.sub(r"\s+", " ", name)

        return name


def rename_movie_folder_and_files(
    directory: Path,
    folder_pattern: str,
    file_pattern: str,
    metadata: MovieMetadata,
    *,
    logger: logging.Logger | None = None,
) -> tuple[bool, Path]:
    """Rename movie folder and files based on NFO metadata and patterns.

    Args:
        directory: Directory containing extracted files
        folder_pattern: Pattern for folder name (e.g., "$T{ ($6)}{ ($Y)}")
        file_pattern: Pattern for file names (e.g., "$T")
        metadata: Movie metadata from NFO
        logger: Optional logger

    Returns:
        Tuple of (success: bool, new_directory: Path)
    """
    if logger is None:
        logger = _logger

    try:
        interpreter = PatternInterpreter(metadata)
        new_directory = directory

        # 1. Rename folder
        if folder_pattern and folder_pattern.strip() != "$D":
            new_folder_name = interpreter.interpret_folder_pattern(folder_pattern)
            if new_folder_name:
                parent_dir = directory.parent
                new_dir = parent_dir / new_folder_name

                if new_dir != directory:
                    try:
                        directory.rename(new_dir)
                        logger.info(
                            "Renamed folder: %s → %s", directory.name, new_folder_name
                        )
                        new_directory = new_dir
                    except OSError as e:
                        logger.warning("Failed to rename folder %s: %s", directory, e)
                        return (False, directory)

        # 2. Rename all files in the directory (but not subdirectories)
        try:
            entries = list(new_directory.iterdir())
        except OSError as e:
            logger.warning("Failed to list files in %s: %s", new_directory, e)
            return (False, new_directory)

        for entry in entries:
            # Skip subdirectories - only rename files
            if not entry.is_file():
                continue

            file_path = entry

            file_ext = file_path.suffix.lower()

            # Get new filename
            new_name_base = interpreter.interpret_file_pattern(
                file_pattern, file_path.name
            )
            new_name = new_name_base + file_ext

            if new_name != file_path.name:
                new_path = new_directory / new_name

                # Handle name conflicts
                if new_path.exists() and new_path != file_path:
                    counter = 1
                    name_stem = new_name_base
                    while new_path.exists():
                        new_name = f"{name_stem} ({counter}){file_ext}"
                        new_path = new_directory / new_name
                        counter += 1

                try:
                    file_path.rename(new_path)
                    logger.info("Renamed file: %s → %s", file_path.name, new_name)
                except OSError as e:
                    logger.warning("Failed to rename file %s: %s", file_path, e)
                    # Continue with other files

        return (True, new_directory)

    except Exception as e:
        logger.error("Error during renaming: %s", e)
        return (False, directory)


__all__ = ["PatternInterpreter", "rename_movie_folder_and_files"]
