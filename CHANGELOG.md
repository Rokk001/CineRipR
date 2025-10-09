# Changelog

All notable changes to this project will be documented in this file.

## [1.0.19] - 2025-01-27

### Fixed
- **CRITICAL FIX:** Windows UNC Path Support - Fixed handling of Windows UNC paths in Docker containers (e.g., `\\HS\Download\dcpp\A.Test.Extract`)
- Added multiple retry strategies for file operations in Docker environments
- Improved path normalization for Windows network shares in Docker containers
- Enhanced error handling and logging for failed file operations
- Added `_safe_move_with_retry()` function with comprehensive fallback strategies

### Changed
- Updated all file move operations to use new safe move function
- Improved Docker container compatibility for Windows network paths
- Enhanced logging for better debugging of file operation failures

## [1.0.18] - 2025-01-08

### Fixed
- **CRITICAL FIX:** Read-only File System Support - Fixed critical issue where file moves would fail on read-only file systems (errno 30)
- Added fallback to copy+delete operations when move operations fail due to read-only file system
- Graceful handling of cases where original files cannot be deleted on read-only file systems
- **CRITICAL FIX:** Subpath Validation Error - Fixed persistent "is not in the subpath" error that was still occurring
- Corrected path validation logic in `move_remaining_to_finished()` function with robust fallback path parsing
- **Docker Permissions:** Set proper file permissions (777) and group ownership ('users') for all extracted and moved files
- Added cross-platform compatibility with proper Unix/Linux vs Windows handling
- Enhanced error handling and logging across all file operations

### Changed
- Updated all file move operations to handle read-only filesystem scenarios
- Improved path validation logic to prevent subpath validation errors
- Added consistent permission management throughout the application

## [1.0.17] - 2025-01-08

### Fixed
- **CRITICAL FIX:** Fixed the "Subpath validation error" that was still occurring in version 1.0.16
- Corrected the archive and file moving logic to properly use only the release name instead of the full relative path
- This resolves the persistent error: `'/data/extracted/Movies/A.Test.Movie' is not in the subpath of '/data/downloads'`
- Fixed all remaining instances where `finished_rel_parent` was incorrectly used instead of `release_name`

### Changed
- Updated all archive group moving logic to consistently use `release_name` instead of `finished_rel_parent`
- Modified file moving logic to extract only the last part of the relative path for the destination directory

## [1.0.16] - 2025-01-08

### Fixed
- **Finished Directory Structure**: Fixed unwanted "Movies" subfolder creation in finished directory
- Files now move directly to `finished/ReleaseName/` instead of `finished/Movies/ReleaseName/`
- Use only release name instead of full path structure for finished directory organization

## [1.0.15] - 2025-01-08

### Fixed
- **Subpath Validation Error**: Fixed "is not in the subpath" error when processing extracted files
- Use `relative_parent` instead of `current_dir.relative_to(download_root)` for proper path handling
- Eliminates "Unexpected error in main loop" when moving files between extracted and finished directories

## [1.0.14] - 2025-01-08

### Fixed
- **Docker Permissions**: Fixed file permissions issue where extracted files were owned by `nobody` user
- Docker container now uses UID/GID 1000 for `cineripr` user to ensure proper file ownership
- Extracted files are now accessible and writable by host users

## [1.0.13] - 2025-01-08

### Fixed
- **CRITICAL FIX**: Progress bar now properly updates the same line instead of creating new lines
- Replaced complex stdout/stderr manipulation with simple print() approach for better compatibility
- Progress bars now work correctly across all terminals and environments (Windows, Linux, Docker)
- Eliminates messy terminal output with multiple progress bar lines
- Much more robust and reliable progress display

## [1.0.12] - 2025-01-08

### Fixed
- Fixed file overwrite behavior in finished directory
- Files now properly overwrite existing files instead of creating duplicates with _1, _2 suffixes
- Eliminates duplicate files in finished directory when processing the same release multiple times

## [1.0.11] - 2025-01-08

### Added
- Display tool name and version at the start of each processing loop
- Clear identification of CineRipR version during execution

### Fixed
- Version synchronization between pyproject.toml and __init__.py
- Consistent version display across all components

## [1.0.10] - 2025-01-08

### Fixed
- Fixed extraction progress bar display for RAR files
- Always show initial progress message when starting extraction
- Show completion message even when 7-Zip doesn't provide detailed progress updates
- Prevent duplicate completion messages in progress tracking
- Ensure progress bar is visible for all RAR extractions regardless of 7-Zip output

## [1.0.9] - 2025-01-08

### Fixed
- Fixed progress bar display for RAR extractions
- Added debug logging for 7-Zip output to troubleshoot progress issues
- Show fallback message when 7-Zip doesn't provide progress information
- Improved progress tracking visibility for RAR extractions

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

