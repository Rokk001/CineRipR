# Changelog

All notable changes to this project will be documented in this file.

## [1.0.8] - 2025-01-08

### Fixed
- Improved error handling for archive file moving to finished directory
- Enhanced logging for move failures with detailed error messages and file paths
- Better debugging information when files fail to move from download to finished directory

### Added
- Debug script for troubleshooting move issues (`debug_move_issue.py`)
- More detailed error reporting in move operations

## [1.0.7] - 2025-01-08

### Added
- Support for .dctmp archive files (temporary archive format)
- Docker permission handling with non-root user
- Automatic file permission correction after extraction
- `fix_file_permissions()` function for Docker environments

### Fixed
- .dctmp files are now properly recognized as archives instead of being copied as regular files
- Docker containers now run as non-root user (cineripr) to prevent permission issues
- Extracted files have correct permissions (644 for files, 755 for directories)
- File permission issues in Docker environments resolved
- Archive files are properly moved to finished directory instead of remaining in extracted folder

### Changed
- Dockerfile now creates and uses non-root user with proper umask settings
- UMASK=002 set for better default permissions in Docker containers
- All extraction methods now fix permissions after successful extraction
- Enhanced Docker documentation with permission troubleshooting guide

## [1.0.0] - 2025-10-07
## [1.0.1] - 2025-10-07
## [1.0.2] - 2025-10-07
## [1.0.3] - 2025-10-07
## [1.0.4] - 2025-10-07

### Added
- Recognize German season folders "Staffel XX" in addition to "Season XX".

### Fixed
- Robust iteration across releases after failures; improved debug logs.
- Repeat mode CLI overrides (`--repeat-forever`, `--repeat-after-minutes`).


### Fixed
- Progress color now changes only between episodes/movies, not for subfolders like `Subs`.

### CI
- Docker workflow hardened with docker/metadata-action and fixed YAML.


### Added
- Endless repeat mode via options: `repeat_forever` and `repeat_after_minutes`

### Changed
- CLI main loop supports periodic re-run based on configuration
- Default configs and README updated accordingly


### Changed
- Project rebranded to CineRipR; primary CLI is now `cineripr`
- Full namespace migration to `cineripr` (legacy name removed)
- Docker support added (Dockerfile, .dockerignore)
- GHCR workflow to build/push images on tags
- README updated with Docker usage and new name


### Breaking/Stable
- First stable release with robust movie and TV-show extraction flows
- Deterministic single-line progress bars for Reading and Extracting

### Added
- `--debug` flag for detailed directory processing logs (off by default)
- Dynamic terminal-width truncation so progress lines never wrap
- Correct handling of modern multi-part RARs (`.partXX.rar`) without base `.rar`
- Windows-friendly inline updates (carriage return + clear line)

### Fixed
- Multi-part extraction shows correct part counters `(X/Y)`
- Reading progress reaches 100% before extraction starts
- Avoids printing repeated lines during extraction
- Season directory recursion and episode extraction logic

### Internal
- Refined archive grouping and validation rules
- Cleaner orchestration for two-phase processing (read then extract)
- Logging format without level prefixes for end-user clarity

## [0.1.0] - 2025-01-06

### Added
- Initial release
- Multi-part archive extraction support (RAR, ZIP, TAR formats)
- Smart TV show organization with Season normalization
- Configurable subfolder policies (Subs, Sample, Other)
- Real-time progress tracking with color-coded progress bars
- Demo mode for testing without filesystem changes
- Automatic cleanup of finished directory based on file age
- Comprehensive CLI with override options
- Support for multiple download root directories
- Flattening of episode directories into season folders

### Features
- **TV Show Organization**: Automatically detects and organizes TV shows into `ShowName/Season XX/` structure
- **Subfolder Management**: Intelligent handling of Subs, Sample, and custom subdirectories
- **Progress Tracking**: Single-line progress updates for multi-part operations, separate lines for completed tasks
- **Error Handling**: Automatic cleanup of partially extracted content on failure
- **Atomic Operations**: All-or-nothing extraction per release to maintain data integrity

### Technical Details
- Python 3.11+ required
- 7-Zip integration for RAR archive support
- TOML-based configuration
- Modular architecture with 6 focused modules:
  - `archive_constants`: Constants and patterns
  - `archive_detection`: Archive discovery and grouping
  - `archive_extraction`: Extraction logic with 7-Zip support
  - `path_utils`: TV show path organization
  - `file_operations`: File/directory management
  - `archives`: Main orchestration

### Code Quality
- Refactored 1204-line monolithic file into 6 maintainable modules
- Comprehensive docstrings for all public functions
- Clear separation of concerns
- Improved testability with focused module boundaries

## [1.0.5] - 2025-10-07
## [1.0.6] - 2025-10-07

### Fixed
- No-season TV shows: derive series folder strictly from the prefix before the episode tag (e.g., `Dragonball.Z.Kai.E001...` -> `Dragonball Z Kai`).
- Ensure Sample folders follow policy strictly (no extraction when disabled).
- TV-tagged parent folders (e.g., `Show.S02...`) correctly recurse and extract nested episode dirs.

### UX
- Tree-style progress: align sibling lines (Processing/Finished/Extracting) on the same level; keep child phases indented.


### Added
- Tree-style progress formatting with visual hierarchy (├─, └──) and consistent indentation.
- Recursive TV-show detection (depth-limited) including short season folders like `S03`.

### Changed
- Reading/Processing/Extracting lines aligned to clear parent/child levels.

### Fixed
- TV shows without explicit season folders: reliably flatten episode folders; move files to series root.
- Episode folders created by archives are flattened even when media is nested in subfolders.
- Treat TV-tagged directories as episodes even if files/archives are one level deeper.
- Include file-only episode directories in contexts.

