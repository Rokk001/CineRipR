# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-01-06

### Added
- Initial release of Emby Extractor
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

