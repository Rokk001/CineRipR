# Refactoring Documentation

## Overview

This document describes the major refactoring efforts in CineRipR:

1. **Core Module Refactoring (v2.0.0):** `archives.py` split into 6 focused modules
2. **WebGUI Refactoring (v2.5.7):** Frontend/Backend separation with Flask Blueprints

---

## 1. Core Module Refactoring (v2.0.0)

The `archives.py` file has been refactored from a monolithic **1204-line file** into **6 focused, maintainable modules**. This improves code organization, testability, and maintainability.

## New Module Structure

### 1. `archive_constants.py` (62 lines)
**Purpose:** Constants and regular expressions

**Contents:**
- Archive format constants (`SUPPORTED_ARCHIVE_SUFFIXES`, `UNWANTED_EXTRACTED_SUFFIXES`)
- Category names (`TV_CATEGORY`, `MOVIES_CATEGORY`)
- Standard subfolder names (`SUBFOLDER_SUBS`, `SUBFOLDER_SAMPLE`, `SUBFOLDER_OTHER`)
- Regular expressions for pattern matching (TV tags, season patterns, multi-part archives)

**Key exports:**
- `SUPPORTED_ARCHIVE_SUFFIXES`
- `TV_TAG_RE`, `SEASON_TAG_RE`, `PART_VOLUME_RE`, `R_VOLUME_RE`

### 2. `archive_detection.py` (217 lines)
**Purpose:** Archive discovery, validation and grouping

**Contents:**
- `ArchiveGroup` dataclass
- Archive format detection (`is_supported_archive`)
- Directory entry splitting (archives vs. other files)
- Multi-part archive grouping (`build_archive_groups`)
- Archive group validation

**Key functions:**
- `is_supported_archive(entry: Path) -> bool`
- `split_directory_entries(directory: Path) -> tuple[list[Path], list[Path]]`
- `build_archive_groups(archives: Sequence[Path]) -> list[ArchiveGroup]`
- `validate_archive_group(group: ArchiveGroup) -> tuple[bool, str | None]`

### 3. `archive_extraction.py` (317 lines)
**Purpose:** Archive extraction and 7-Zip handling

**Contents:**
- Archive format detection
- 7-Zip executable resolution
- RAR extraction with progress tracking
- Fallback extraction to temporary directory (for long paths)
- Generic archive extraction

**Key functions:**
- `detect_archive_format(archive: Path) -> str | None`
- `resolve_seven_zip_command(seven_zip_path: Path | None) -> str | None`
- `can_extract_archive(archive: Path, *, seven_zip_path: Path | None) -> tuple[bool, str | None]`
- `extract_archive(archive: Path, target_dir: Path, ...) -> None`

### 4. `path_utils.py` (178 lines)
**Purpose:** Path utilities for TV show organization

**Contents:**
- Season directory detection
- TV show path building (with "Season XX" format)
- Special subdirectory normalization (Subs, Sample, etc.)
- TV show vs. movie categorization

**Key functions:**
- `is_season_directory(directory: Path) -> bool`
- `extract_season_from_tag(name: str) -> str | None`
- `build_tv_show_path(base_dir: Path, download_root: Path, base_prefix: Path) -> Path`
- `normalize_special_subdir(name: str) -> str | None`
- `looks_like_tv_show(root: Path) -> bool`
- `get_category_prefix(directory: Path) -> Path`

### 5. `file_operations.py` (207 lines)
**Purpose:** File and directory operations

**Contents:**
- Unique destination path generation
- Extraction failure cleanup
- Empty directory tree removal
- Single subdirectory flattening
- Companion file copying
- Archive group moving

**Key functions:**
- `ensure_unique_destination(destination: Path) -> Path`
- `cleanup_failed_extraction_dir(target_dir: Path, *, pre_existing: bool) -> None`
- `handle_extraction_failure(...) -> bool`
- `remove_empty_tree(directory: Path, *, stop: Path) -> None`
- `flatten_single_subdir(directory: Path) -> None`
- `copy_non_archives_to_extracted(current_dir: Path, target_dir: Path) -> None`
- `move_archive_group(...) -> list[Path]`
- `move_remaining_to_finished(...) -> None`

### 6. `archives.py` (505 lines)
**Purpose:** Main orchestration and workflow

**Contents:**
- `ProcessResult` dataclass
- Download directory iteration
- Release context building
- Main processing workflow (`process_downloads`)

**Key functions:**
- `iter_download_subdirs(download_root: Path) -> list[Path]`
- `process_downloads(paths: Paths, ...) -> ProcessResult`

## Benefits of Refactoring

### 1. **Improved Maintainability**
- Each module has a single, clear responsibility
- Easier to locate and modify specific functionality
- Better code organization with logical grouping

### 2. **Better Testability**
- Smaller, focused modules are easier to unit test
- Clear interfaces between modules
- Reduced dependencies within each module

### 3. **Enhanced Readability**
- Descriptive module names clearly indicate purpose
- Shorter files are easier to navigate
- Comprehensive docstrings for all public functions

### 4. **Easier Collaboration**
- Multiple developers can work on different modules simultaneously
- Merge conflicts are less likely
- Clearer code review boundaries

### 5. **Reduced Complexity**
- Original 1204-line file split into manageable chunks
- Average module size: ~215 lines
- Clear separation of concerns

## Migration Notes

### Import Changes
Code that previously imported from `archives.py` may need updates:

**Before:**
```python
from .archives import (
    ArchiveGroup,
    build_archive_groups,
    extract_archive,
    can_extract_archive,
)
```

**After:**
```python
from .archive_detection import ArchiveGroup, build_archive_groups
from .archive_extraction import extract_archive, can_extract_archive
```

However, the main entry point (`process_downloads`) remains in `archives.py`, so most external code should continue to work without changes.

### Backward Compatibility
- All public APIs remain unchanged
- `archives.py` still exports main functions for backward compatibility
- Existing CLI and configuration continue to work

## File Size Comparison

| File                    | Lines | Purpose            |
| ----------------------- | ----- | ------------------ |
| **Before**              |       |                    |
| `archives.py`           | 1204  | Everything         |
| **After**               |       |                    |
| `archive_constants.py`  | 62    | Constants & regex  |
| `archive_detection.py`  | 217   | Archive discovery  |
| `archive_extraction.py` | 317   | Extraction logic   |
| `path_utils.py`         | 178   | Path handling      |
| `file_operations.py`    | 207   | File operations    |
| `archives.py`           | 505   | Main orchestration |
| **Total**               | 1486  | (includes docs)    |

*Note: Line count increased slightly due to comprehensive docstrings and module headers.*

## Testing Recommendations

After refactoring, focus testing on:

1. **Integration tests**: Verify `process_downloads` workflow still works correctly
2. **Unit tests**: Test individual modules in isolation
3. **Edge cases**: Multi-part archives, TV show path building, extraction failures
4. **Regression tests**: Ensure all previous bugs remain fixed

## Future Improvements

With this new structure, future enhancements become easier:

1. **Add new archive formats**: Modify only `archive_detection.py` and `archive_extraction.py`
2. **Enhance TV show detection**: Modify only `path_utils.py`
3. **Improve error handling**: Modify only `file_operations.py`
4. **Add new features**: Clear module boundaries make it obvious where to add code

---

## 2. WebGUI Refactoring (v2.5.7)

The `webgui.py` file has been refactored from a monolithic **2752-line file** into a modern, maintainable structure with complete Frontend/Backend separation.

### New Structure

**Before:**
- `webgui.py` = 2752 Zeilen (alles in einer Datei)
  - HTML, CSS, JavaScript in Python-Strings
  - Alle Routes in einer Funktion
  - Schwer zu warten und zu testen

**After:**
```
src/cineripr/web/
├── app.py                    # Flask App Factory (30 Zeilen)
├── webgui.py                 # Legacy wrapper (vereinfacht)
├── routes/                   # Flask Blueprints
│   ├── views.py             # HTML Views (32 Zeilen)
│   ├── api.py               # API Routes (137 Zeilen)
│   └── settings.py          # Settings Routes (106 Zeilen)
├── templates/               # HTML Templates
│   └── index.html           # Dashboard Template (1242 Zeilen)
├── static/                  # Static Files
│   ├── css/style.css        # CSS Styles (1215 Zeilen)
│   ├── js/app.js            # JavaScript (760 Zeilen)
│   └── favicon.svg          # Favicon
└── services/                # Services Layer
    └── status_tracker.py     # Status Tracker Wrapper
```

### Key Improvements

1. **Frontend/Backend Separation:**
   - HTML in `templates/index.html`
   - CSS in `static/css/style.css`
   - JavaScript in `static/js/app.js`
   - Favicon in `static/favicon.svg`

2. **Flask Blueprints:**
   - `views_bp` für HTML-Seiten
   - `api_bp` für API-Endpunkte
   - `settings_bp` für Settings-Verwaltung

3. **Flask App Factory:**
   - `create_app()` für zentrale App-Erstellung
   - Tracker-Initialisierung mit DB-Werten
   - Blueprint-Registrierung

### Benefits

1. **Maintainability:** HTML/CSS/JS in separate files with syntax highlighting
2. **Testability:** Blueprints can be tested individually
3. **Scalability:** Easy to add new routes
4. **Best Practices:** Follows Flask standards
5. **Developer Experience:** Code completion, syntax highlighting, debugging

### Backward Compatibility

- **No Breaking Changes:** All imports work as before
- `webgui.py` remains as legacy wrapper
- `create_app()` and `run_webgui()` work as before
- All API endpoints remain unchanged

---

## Conclusion

These refactorings significantly improve code quality while maintaining all existing functionality. The modular structure provides a solid foundation for future development and maintenance.

