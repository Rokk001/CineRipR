# Finished Path Logic Documentation

## Overview

This document explains how CineRipR moves files from the `extracted` directory to the `finished` directory, including the logic for organizing TV shows and movies.

## Process Flow

1. **Extraction Phase**: Files are first extracted to the `extracted` directory with proper TV show structure
2. **Move Phase**: After successful extraction, files are moved from `extracted` to `finished` directory
3. **Cleanup Phase**: Original archive files are moved to `finished` directory

## TV Show Organization

### Input Structure (from downloads)
```
Download/
  Show.Name.S01.GROUP/
    Show.Name.S01E05.GROUP/
      episode-archive.part01.rar
      episode-archive.part02.rar
```

### Extracted Structure (temporary)
```
Extracted/
  TV-Shows/
    Show Name/
      Season 01/
        Show.Name.S01E05.GROUP.mkv
        Show.Name.S01E05.GROUP.nfo
```

### Finished Structure (final)
```
Finished/
  TV-Shows/
    Show Name/
      Season 01/
        Show.Name.S01E05.GROUP.mkv
        Show.Name.S01E05.GROUP.nfo
```

## Movie Organization

### Input Structure
```
Download/
  Movie.Name.2024.GROUP/
    movie-archive.part01.rar
    movie-archive.part02.rar
```

### Finished Structure
```
Finished/
  Movies/
    Movie.Name.2024.GROUP/
      Movie.Name.2024.GROUP.mkv
      Movie.Name.2024.GROUP.nfo
```

## Key Functions

### `move_remaining_to_finished()`

This function handles moving files from `extracted` to `finished` directory:

1. **TV Show Detection**: Uses `looks_like_tv_show()` to determine if content is a TV show
2. **Path Building**: 
   - For TV shows: Uses `build_tv_show_path()` to create proper `TV-Shows/Show Name/Season XX/` structure
   - For movies: Uses original release name structure
3. **File Movement**: Uses `_safe_move_with_retry()` for Docker/UNC path compatibility
4. **Permission Setting**: Sets proper permissions (777) and group ownership ('users')

### TV Show Path Building Logic

The `build_tv_show_path()` function:

1. **Season Detection**: Finds season tags (S01, S02, etc.) in directory names
2. **Show Name Extraction**: Extracts show name by removing season/episode tags
3. **Normalization**: Converts to `Show Name/Season XX/` format
4. **Flattening**: Removes unnecessary nested episode directories

### Example Transformations

| Input Path                                       | Output Path                                         |
| ------------------------------------------------ | --------------------------------------------------- |
| `Show.Name.S01.GROUP`                            | `TV-Shows/Show Name/Season 01/`                     |
| `Another.Show.S02.GROUP`                         | `TV-Shows/Another Show/Season 02/`                  |
| `Movie.Name.2024.GROUP`                          | `Movies/Movie.Name.2024.GROUP/`                     |

## Error Handling

### UNC Path Support
- Detects Windows UNC paths (e.g., `\\SERVER\Share\...`)
- Normalizes paths for Docker container compatibility
- Uses multiple retry strategies for file operations

### Read-Only File Systems
- Detects read-only file system errors (errno 30)
- Falls back to copy+delete operations
- Handles cases where original files cannot be deleted

### Permission Issues
- Sets file permissions to 777 for all moved files
- Sets group ownership to 'users' when available
- Provides cross-platform compatibility

## Configuration

The finished path logic respects the following configuration:

- `paths.finished_root`: Root directory for finished files
- `paths.extracted_root`: Temporary extraction directory
- `subfolders.*`: Policies for handling Subs, Sample, and other subdirectories

## Debugging

To debug finished path issues:

1. Enable debug mode: `--debug`
2. Check logs for path building decisions
3. Verify TV show detection logic
4. Test with demo mode: `--demo`

## Common Issues

### Files Not Moving
- Check UNC path handling in Docker containers
- Verify read-only file system fallback
- Ensure proper permissions on destination directories

### Wrong TV Show Structure
- Verify season tag detection (S01, S02, etc.)
- Check show name extraction logic
- Ensure proper category prefix detection

### Permission Errors
- Verify group 'users' exists in container
- Check file system permissions
- Ensure proper UMASK settings in Docker
