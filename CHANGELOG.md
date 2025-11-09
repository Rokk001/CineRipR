# Changelog

All notable changes to this project will be documented in this file.

## [1.0.36] - 2025-11-09

### Added
- **Release Detail View**: Click on any queue item to view detailed information in a modal dialog
  - View release status, archive count, start time, and duration
  - See current archive being processed with progress
  - Filter logs specific to that release
  - Keyboard shortcut (ESC) to close modal
- **Timeline/History View**: New "History" tab showing processed releases
  - Visual timeline with color-coded success/failure markers
  - Display duration, archive count, and completion status
  - Animated entry with smooth transitions
- **Manual Control Panel**: Pause and resume processing on demand
  - Visual pause/resume buttons with gradient styling
  - Status indicator showing current processing state
  - Automatic button state updates based on processing status
- **Dark/Light Mode Toggle**: Switch between dark and light themes
  - Theme preference saved to localStorage and server
  - Smooth CSS transitions between themes
  - Full CSS variable system for theming
  - Theme persists across page reloads
- **CPU & Memory Monitoring**: Real-time system resource tracking
  - Display current CPU usage percentage
  - Display current memory usage percentage
  - Updated every 2 seconds alongside other system health metrics
- **Toast Sound Notifications**: Optional audio alerts for notifications
  - Different tones for success, error, warning, and info
  - Two-tone notification sounds using Web Audio API
  - Configurable via localStorage (soundEnabled)
  - Automatically plays on toast notifications

### Changed
- Complete frontend architecture overhaul for improved modularity
- Enhanced modal system with better animations and keyboard controls
- Improved status tracking with pause/resume state management
- Extended StatusTracker with history, theme, and control endpoints
- Better responsive design for all screen sizes
- Improved header layout with theme toggle button
- Updated all cards and components to use CSS variables for theming

### Backend
- Extended `StatusTracker` with `ReleaseHistory` dataclass
- Added `is_paused`, `history`, and `theme_preference` to GlobalStatus
- New methods: `add_to_history()`, `set_theme()`, `pause_processing()`, `resume_processing()`
- Enhanced `update_system_health()` to include CPU and memory monitoring via psutil
- New API endpoints:
  - `/api/theme` (GET/POST) for theme management
  - `/api/control/pause` (POST) to pause processing
  - `/api/control/resume` (POST) to resume processing
  - `/api/history` (GET) to retrieve processing history
- Updated `/api/notifications/<notif_id>/read` endpoint

## [1.0.35] - 2025-11-09

### Added
- **Toast Notifications**: Real-time pop-up notifications for important events
- **Processing Queue Display**: See all pending archives waiting for processing
- **Log Filtering & Search**: Filter logs by level and search through log history
- **System Health Monitoring**: Real-time disk space monitoring for all paths
- **Tab Navigation**: Clean organization with Overview, Queue, System Health, and Logs tabs
- **Favicon**: Browser tab icon with CineRipR branding
- **7-Zip Version Display**: Shows installed 7-Zip version in System Health

### Changed
- Complete WebGUI restructuring with tab-based navigation
- Improved status consistency (no more "Idle" with "Processing..." displayed)
- Better mobile responsiveness
- Cleaner, less overwhelming interface layout

### Fixed
- Status display inconsistencies between running and idle states
- Current release cleared when processing completes

## [1.0.34] - 2025-01-27

### Changed
- **Modernized WebGUI Design**: Complete visual overhaul with modern UI/UX
  - Glassmorphism effects with backdrop blur
  - Dark theme with gradient backgrounds
  - Animated background particles
  - Smooth transitions and hover effects
  - Better card designs with accent colors
  - Animated progress bar with shimmer effect
  - Improved status indicators with pulse and ripple animations
  - Enhanced responsive design for mobile devices
  - Better typography with Inter font family
  - Auto-scrolling logs with smooth animations

## [1.0.33] - 2025-01-27

### Fixed
- **Critical RAR extraction fix**: Replaced p7zip-full with official 7-Zip binary
  - p7zip-full does not support all RAR compression methods (caused "Unsupported Method" errors)
  - Official 7-Zip 24.09 Linux binary now supports all RAR formats including RAR5
  - Multi-volume RAR archives now extract correctly in Docker container

### Changed
- Dockerfile now downloads and installs official 7-Zip binary instead of p7zip-full package
- Created symlink from `7zz` to `7z` for compatibility

## [1.0.32] - 2025-01-27

### Changed
- WebGUI is now enabled by default (no --webgui flag required)
- Use --no-webgui to disable WebGUI if needed
- Improved WebGUI error handling and logging

## [1.0.31] - 2025-01-27

### Fixed
- WebGUI now runs as non-daemon thread to prevent premature termination
- Main thread now waits for WebGUI when active (prevents connection refused errors)
- WebGUI remains accessible even when processing is complete

## [1.0.30] - 2025-01-27

### Added
- WebGUI for status monitoring and progress tracking (default port 8080)
- Multi-volume RAR validation: checks if all volumes are present before extraction
- Status tracking API endpoints (`/api/status`, `/api/health`)
- Real-time progress updates in WebGUI dashboard
- CLI options: `--webgui`, `--webgui-port`, `--webgui-host`

### Fixed
- Multi-volume RAR extraction now properly validates volume count before attempting extraction
- Prevents "Unsupported Method" errors when volumes are missing

### Changed
- Added Flask dependency for WebGUI functionality
- Dockerfile exposes port 8080 for WebGUI access

### Removed
- Debug scripts: `debug_extraction_issue.py`, `debug_move_issue.py`, `METADATA_INTEGRATION_EXAMPLE.py`
- Unused imports cleaned up across codebase

## [1.0.29] - 2025-10-10

### Fixed
- Extracted TV shows: derive show name correctly when season folders (e.g., `S01`) are present; target `_extracted/TV-Shows/<Series>/Season XX/...`
- Ensure related episode artifacts in sibling folders (`Subs`, `Sample`, `Sonstige`, `Proof`) are moved alongside the episode to finished

### Notes
- If no valid archive groups are found for a context, extraction is skipped with an error log (likely incomplete download)
- Finished archiving logic remains unchanged

## [1.0.28] - 2025-10-10

### Fixed
- Use `TV-Shows` (plural) as extracted category name
- Correct show-name derivation when season folder like `S01` is present: place under `<Series>/Season 01`, not under `S01/Season 01`
- Skip extraction when no valid archive groups are found (likely incomplete download); log error only

### Notes
- Finished archiving logic unchanged (1:1 mirror of downloads)

## [1.0.27] - 2025-10-10

### Fixed
- Extraction path category restored: TV shows extract under `TV-Show/`, movies under `Movies/`
- Example: `_extracted/TV-Show/<Series>/Season XX/...` and `_extracted/Movies/<Release>/...`

### Notes
- Finished archiving logic remains unchanged (1:1 mirror of downloads)

## [1.0.26] - 2025-10-10

### Fixed
- Extraction path for series restored: extracted now uses `<extracted_root>/<Series>/Season XX/...` (no seasons at extracted root)
- Change limited strictly to extraction target computation; finished archiving logic unchanged

### Notes
- Finished still mirrors downloads 1:1 under `<finished>/<ReleaseRoot>/...`

## [1.0.25] - 2025-10-10

### Fixed
- Finished move for series: season folders now land under `<ReleaseName>/Season XX` instead of at the finished root
- Robust release-root derivation for mirroring download structure

### Changed
- No change in extracted behavior; extracted remains final for extracted content

## [1.0.24] - 2025-10-10

### Fixed
- Finished move now mirrors the release directory from downloads 1:1 under `finished/<ReleaseName>/` for both movies and series
- Removed unintended movement of extracted content into finished
- Ensured companions (`Sample`, `Subs`, etc.) are preserved exactly as in downloads during move

### Changed
- Simplified move logic to avoid TV-specific restructuring in finished

## [1.0.23] - 2025-01-27

### Fixed
- **CRITICAL FIX:** Archive Movement Logic - Corrected implementation of archive file movement
- Fixed confusion about what gets moved to finished directory
- Original archive files (e.g., .rar) are now correctly moved from download/ to finished/ after extraction
- Extracted content remains in extracted/ directory as intended
- Clarified the two-step process: extract content to extracted/, then move original archives to finished/

### Changed
- Updated `process_downloads()` to use `move_archive_group()` for moving original archive files
- Improved documentation and comments to clarify the extraction vs. movement process
- Enhanced project documentation to prevent future confusion about file movement logic

### Added
- Clear documentation of the two-step process in PROJECT_STATUS.md
- Updated version tracking and project structure documentation

## [1.0.22] - 2025-01-27

### Fixed
- **CRITICAL FIX:** Removed all chown commands that were causing errors in Docker containers
- Fixed 'PosixPath' object has no attribute 'chown' error
- Simplified permission handling to only set chmod 777, no group ownership changes
- Removed unused imports and cleaned up code

### Changed
- Permission setting now only uses chmod 777 without chown operations
- Removed dependency on grp and pwd modules for group ownership
- Simplified _set_file_permissions() function to avoid Docker permission issues

## [1.0.21] - 2025-01-27

### Fixed
- **CRITICAL FIX:** Fixed files being moved with 1:1 download structure instead of proper TV show organization
- Fixed issue where non-archive files were bypassing the proper TV show path building logic
- Updated `process_downloads()` to use `move_remaining_to_finished()` for all file moves
- Ensures TV shows follow the correct `TV-Shows/Show Name/Season XX/` structure

### Changed
- All file moves now use the centralized `move_remaining_to_finished()` function
- Removed duplicate file moving logic that was creating incorrect folder structures
- Improved consistency between archive and non-archive file handling

## [1.0.20] - 2025-01-27

### Fixed
- **CRITICAL FIX:** TV Show Organization - Fixed TV show extraction and finished path logic
- TV shows now properly follow README specification: `TV-Shows/Show Name/Season XX/`
- Fixed issue where TV shows were not using proper folder structure in finished directory
- Enhanced `move_remaining_to_finished()` to detect TV shows and use correct path building
- Added comprehensive documentation for finished path logic

### Changed
- Updated TV show path building to use existing `build_tv_show_path()` logic
- Improved finished directory organization for both TV shows and movies
- Enhanced error handling and fallback logic for path building

### Added
- `FINISHED_PATH_LOGIC.md` - Complete documentation of finished path logic
- Detailed explanation of TV show vs movie organization
- Debugging guide for finished path issues

## [1.0.19] - 2025-01-27

### Fixed
- **CRITICAL FIX:** Windows UNC Path Support - Fixed handling of Windows UNC paths in Docker containers
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

