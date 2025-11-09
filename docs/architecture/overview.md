# CineRipR - Architecture Overview

## System Architecture

### High-Level Flow
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│  Downloads  │───▶│   Extract    │───▶│  Organize   │───▶│  Finished   │
│  Directory  │    │  Archives    │    │ TV/Movies   │    │  Directory  │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
   Archive Files      Extracted Files    Structured Files    Final Files
   (.rar, .zip)       (.mkv, .nfo)       (TV/Movie)         (Ready for Plex)
```

### Module Dependencies
```
archives.py (Main Orchestrator)
├── file_operations.py
│   ├── path_utils.py
│   └── archive_detection.py
├── archive_extraction.py
├── config.py
└── progress.py
```

## Core Components

### 1. Archives Module (`archives.py`)
**Purpose**: Main orchestration and workflow management
**Key Functions**:
- `process_downloads()`: Main entry point
- `iter_download_subdirs()`: Directory scanning
- `_iter_release_directories()`: Release processing

**Responsibilities**:
- Coordinate entire extraction workflow
- Manage progress tracking
- Handle error recovery
- Orchestrate file movements

### 2. File Operations (`file_operations.py`)
**Purpose**: File and directory operations with Docker/UNC support
**Key Functions**:
- `move_remaining_to_finished()`: Central finished path logic
- `_safe_move_with_retry()`: Docker-safe file operations
- `_set_file_permissions()`: Permission management
- `copy_non_archives_to_extracted()`: Companion file handling

**Responsibilities**:
- Safe file operations in Docker environments
- UNC path handling for Windows network shares
- Permission management (chmod only, no chown)
- Error handling for read-only filesystems

### 3. Path Utilities (`path_utils.py`)
**Purpose**: TV show detection and path organization
**Key Functions**:
- `looks_like_tv_show()`: TV show detection
- `build_tv_show_path()`: TV show path construction
- `get_category_prefix()`: Category determination
- `extract_season_from_tag()`: Season extraction

**Responsibilities**:
- Detect TV shows vs movies
- Build proper TV show folder structure
- Extract season/episode information
- Normalize show names

### 4. Archive Extraction (`archive_extraction.py`)
**Purpose**: Archive format handling and extraction
**Key Functions**:
- `extract_archive()`: Main extraction logic
- `can_extract_archive()`: Pre-extraction validation
- `_extract_with_7zip()`: 7-Zip integration
- `_extract_with_python()`: Python-native extraction

**Responsibilities**:
- Support multiple archive formats (RAR, ZIP, TAR)
- Handle multi-part archives
- Integrate with 7-Zip for RAR support
- Provide fallback extraction methods

### 5. Archive Detection (`archive_detection.py`)
**Purpose**: Archive group detection and validation
**Key Functions**:
- `build_archive_groups()`: Group detection
- `validate_archive_group()`: Group validation
- `split_directory_entries()`: File categorization
- `ArchiveGroup`: Data structure for archive groups

**Responsibilities**:
- Detect multi-part archives
- Group related archive files
- Validate archive completeness
- Handle various naming conventions

## Data Flow

### 1. Scanning Phase
```
Downloads Directory
├── Scan for archive files
├── Group multi-part archives
├── Detect TV shows vs movies
└── Build processing contexts
```

### 2. Extraction Phase
```
Archive Groups
├── Validate completeness
├── Extract to temporary directory
├── Copy companion files
└── Flatten episode directories
```

### 3. Organization Phase
```
Extracted Files
├── Detect content type (TV/Movie)
├── Build proper folder structure
├── Apply naming conventions
└── Handle subfolders (Subs, Sample)
```

### 4. Movement Phase
```
Organized Files
├── Move to finished directory
├── Apply proper permissions
├── Clean up temporary files
└── Move original archives
```

## Configuration System

### Configuration Priority (v2.3.0+)

Settings are loaded in the following priority order:

1. **WebGUI Settings (SQLite)** - Highest priority
   - Configured via WebGUI at http://localhost:8080
   - Stored in SQLite database (`/config/cineripr_settings.db`)
   - Overrides all other settings

2. **CLI Arguments** - Second priority
   - Override settings via command-line
   - Required for paths if no TOML file

3. **TOML File** (Optional) - Third priority
   - Legacy configuration file
   - Only used if provided via `--config`

4. **Defaults** - Lowest priority
   - Built-in default values

### TOML Configuration (Optional)

```toml
[paths]
download_roots = ["/data/downloads"]
extracted_root = "/data/extracted"
finished_root = "/data/finished"

[options]
finished_retention_days = 15
enable_delete = false
demo_mode = false

[subfolders]
include_sample = false
include_sub = false
include_other = false

[tools]
seven_zip = "/usr/bin/7z"
```

### CLI Arguments

- Paths can be set via CLI args: `--download-root`, `--extracted-root`, `--finished-root`
- All other settings can be overridden via command line
- Supports multiple download roots
- Demo mode for testing
- Debug mode for troubleshooting

### WebGUI Configuration

- All settings manageable via WebGUI (v2.3.0+)
- Settings stored in SQLite database
- No TOML file required for Docker deployments
- Settings persist across container restarts

## Error Handling Strategy

### 1. Archive-Level Errors
- **Incomplete Archives**: Skip and log
- **Corrupted Archives**: Skip and log
- **Unsupported Formats**: Skip and log

### 2. File System Errors
- **Read-only Filesystem**: Copy+delete fallback
- **Permission Errors**: Log and continue
- **Path Errors**: Fallback path extraction

### 3. Docker-Specific Errors
- **UNC Path Issues**: Path normalization
- **Permission Issues**: chmod only, no chown
- **Container Limits**: Graceful degradation

## Performance Considerations

### 1. Parallel Processing
- Multiple archive groups processed simultaneously
- CPU core utilization for extraction
- Progress tracking for user feedback

### 2. Memory Management
- Stream processing for large files
- Temporary file cleanup
- Efficient path operations

### 3. I/O Optimization
- Batch file operations
- Minimize filesystem calls
- Efficient directory traversal

## Security & Privacy

### 1. Path Sanitization
- No private paths in logs or releases
- Generic examples only
- Mandatory path scanning

### 2. Docker Security
- Non-root execution
- Minimal permissions
- Read-only mounts where possible

### 3. Error Information
- No sensitive data in error messages
- Generic error descriptions
- Safe logging practices

## Testing Strategy

### 1. Unit Tests
- Individual function testing
- Mock file system operations
- Error condition testing

### 2. Integration Tests
- End-to-end workflow testing
- Docker container testing
- Real archive processing

### 3. Performance Tests
- Large archive handling
- Memory usage monitoring
- I/O performance measurement

## Deployment Considerations

### 1. Docker Deployment
- Multi-platform support (amd64, arm64)
- Automated builds via GitHub Actions
- Health checks and monitoring

### 2. Local Deployment
- Python 3.11+ requirement
- 7-Zip dependency for RAR support
- Cross-platform compatibility

### 3. Configuration Management
- Environment-specific configs
- Secret management
- Logging configuration

## Monitoring & Logging

### 1. Progress Tracking
- Real-time progress bars
- Color-coded progress indicators
- Detailed operation logging

### 2. Error Reporting
- Structured error logging
- Debug mode for troubleshooting
- Performance metrics

### 3. Audit Trail
- Complete operation history
- File movement tracking
- Configuration changes

## Future Enhancements

### 1. Performance
- Async file operations
- Better parallel processing
- Memory optimization

### 2. Features
- Additional archive formats
- Custom naming rules
- Advanced filtering

### 3. Integration
- Webhook notifications
- API endpoints
- Database integration
