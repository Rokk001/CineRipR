# Release Notes - CineRipR 1.0.18

## Fixed

### Critical Fixes
- **Read-only File System Support**: Fixed critical issue where file moves would fail on read-only file systems (errno 30)
  - Added fallback to copy+delete operations when move operations fail due to read-only file system
  - Graceful handling of cases where original files cannot be deleted on read-only file systems
  - Applied to all file move operations throughout the application

- **Subpath Validation Error**: Fixed persistent "is not in the subpath" error that was still occurring
  - Corrected path validation logic in `move_remaining_to_finished()` function
  - Added robust fallback path parsing for files in extracted directories
  - Eliminates "Unexpected error in main loop" when processing files between extracted and finished directories

### File Permissions & Ownership
- **Docker Permissions**: Set proper file permissions (777) and group ownership ('users') for all extracted and moved files
  - Added `_set_file_permissions()` helper function for consistent permission management
  - Cross-platform compatibility with proper Unix/Linux vs Windows handling
  - Applied to all file operations: copying, moving, and archiving

### Error Handling Improvements
- **Enhanced Error Resilience**: Improved error handling across all file operations
  - Better logging for troubleshooting read-only file system issues
  - Graceful degradation when permission changes fail
  - More informative error messages for debugging

## Technical Details

### Files Modified
- `src/cineripr/archives.py`: Enhanced move operations with read-only filesystem support and permission fixes
- `src/cineripr/file_operations.py`: Added permission management and robust path handling
- `pyproject.toml`: Version bump to 1.0.18
- `src/cineripr/__init__.py`: Version bump to 1.0.18

### Key Improvements
1. **Read-only Filesystem Compatibility**: Application now works properly in Docker environments with read-only file systems
2. **Consistent Permissions**: All extracted and moved files now have proper 777 permissions and 'users' group ownership
3. **Path Validation**: Fixed subpath validation errors that were causing application crashes
4. **Cross-platform Support**: Proper handling of Unix/Linux vs Windows differences in file operations

## Migration Notes

No configuration changes required. This release is fully backward compatible.

## Docker Users

This release specifically addresses Docker environment issues:
- Read-only file system errors are now handled gracefully
- File permissions are properly set for host system access
- Group ownership is set to 'users' for better compatibility

## Testing

The fixes have been tested to resolve:
- "Read-only file system" errors during file moves
- "is not in the subpath" validation errors
- File permission issues in Docker environments
- Cross-platform compatibility issues
