# CineRipR Release 1.0.7

**Release Date:** 2025-01-08  
**Version Type:** Patch Release  
**Compatibility:** Python 3.11+

## 🎯 Overview

This patch release addresses critical issues with Docker deployments and adds support for a new archive format. The main focus is on fixing file permission problems that occur when running CineRipR in Docker containers.

## 🆕 New Features

### .dctmp Archive Support
- **Added support for .dctmp files** - temporary archive format commonly used by download clients
- These files are now properly recognized as archives instead of being treated as regular files
- Full extraction support using 7-Zip backend

### Docker Permission Management
- **Non-root user execution** - Docker containers now run as `cineripr` user instead of root
- **Automatic permission correction** - All extracted files get proper permissions (644 for files, 755 for directories)
- **UMASK configuration** - Set to 002 for better default permissions in containerized environments

## 🐛 Bug Fixes

### Critical Fixes
- **Fixed .dctmp file handling** - These files were previously copied to the extracted folder instead of being processed as archives
- **Resolved Docker permission issues** - Extracted files are no longer read-only for normal users
- **Archive cleanup** - Archive files are now properly moved to finished directory instead of remaining in extracted folder

### Docker Improvements
- **Container security** - Non-root execution reduces security risks
- **File ownership** - Extracted files have correct ownership and permissions
- **Cross-platform compatibility** - Better handling of file permissions across different systems

## 🔧 Technical Changes

### Code Enhancements
- New `fix_file_permissions()` function for automatic permission correction
- Enhanced `detect_archive_format()` to recognize .dctmp files
- Updated `can_extract_archive()` and `extract_archive()` for .dctmp support
- Improved `copy_non_archives_to_extracted()` with permission handling

### Docker Configuration
- Updated Dockerfile with non-root user creation
- Added proper umask settings (UMASK=002)
- Enhanced container security and file handling

## 📋 Migration Guide

### For Docker Users
1. **Rebuild your Docker image:**
   ```bash
   docker build -t cineripr:latest .
   ```

2. **Fix existing files with wrong permissions:**
   ```bash
   find /path/to/extracted -type f -exec chmod 644 {} \;
   find /path/to/extracted -type d -exec chmod 755 {} \;
   ```

3. **Update your docker run command** (no changes needed - same syntax)

### For .dctmp File Users
- No configuration changes required
- .dctmp files will now be automatically detected and processed as archives
- Existing .dctmp files in extracted folders should be moved to finished directory

## 🚀 Installation

### From Source
```bash
git clone https://github.com/Rokk001/CineRipR.git
cd CineRipR
pip install .
```

### Docker
```bash
docker pull ghcr.io/rokk001/cineripr:1.0.7
```

## 📖 Documentation Updates

- Added `DOCKER_PERMISSIONS.md` with comprehensive Docker permission troubleshooting
- Updated README with Docker permission information
- Enhanced inline code documentation

## 🔍 Testing

This release has been tested with:
- Various .dctmp archive formats
- Docker containers on Linux and Windows
- File permission scenarios
- Multi-part archive extraction
- TV show and movie organization

## 🐛 Known Issues

None identified in this release.

## 📞 Support

If you encounter any issues with this release:
1. Check the `DOCKER_PERMISSIONS.md` guide for Docker-related problems
2. Review the CHANGELOG.md for detailed change information
3. Open an issue on GitHub with detailed error information

## 🙏 Acknowledgments

Thanks to the community for reporting the Docker permission issues and .dctmp file handling problems that led to this release.

---

**Full Changelog:** https://github.com/Rokk001/CineRipR/compare/1.0.6...1.0.7
