# Release 1.0.7 Checklist

## ✅ Completed Tasks

### Version Updates
- [x] Updated `pyproject.toml` version to 1.0.7
- [x] Updated `CHANGELOG.md` with new version entry
- [x] Created detailed release notes in `RELEASE_NOTES_1.0.7.md`

### Documentation Updates
- [x] Updated `README.md` with Docker features and version references
- [x] Created `DOCKER_PERMISSIONS.md` with comprehensive troubleshooting guide
- [x] Created release creation scripts (`create_release.ps1` and `create_release.sh`)

### Code Changes
- [x] Added .dctmp archive support in `archive_detection.py`
- [x] Enhanced `archive_extraction.py` with .dctmp handling
- [x] Added `fix_file_permissions()` function for Docker environments
- [x] Updated Dockerfile with non-root user and proper umask
- [x] Enhanced file permission handling in `file_operations.py`

## 🚀 Release Process

### 1. Pre-Release Verification
```powershell
# Check git status
git status

# Verify all changes are committed
git diff --cached

# Run tests (if available)
# pytest tests/
```

### 2. Create Release
```powershell
# Dry run first
.\create_release.ps1 -DryRun

# Create actual release
.\create_release.ps1
```

### 3. GitHub Release
1. Go to: https://github.com/Rokk001/CineRipR/releases
2. Click "Create a new release"
3. Select tag: `v1.0.7`
4. Title: `CineRipR 1.0.7 - Docker Permissions & .dctmp Support`
5. Copy content from `RELEASE_NOTES_1.0.7.md`
6. Mark as "Latest release"
7. Publish release

### 4. Docker Release
```bash
# Build and push Docker image
docker build -t ghcr.io/rokk001/cineripr:1.0.7 .
docker push ghcr.io/rokk001/cineripr:1.0.7

# Update latest tag
docker tag ghcr.io/rokk001/cineripr:1.0.7 ghcr.io/rokk001/cineripr:latest
docker push ghcr.io/rokk001/cineripr:latest
```

## 📋 Release Summary

**Version:** 1.0.7  
**Type:** Patch Release  
**Date:** 2025-01-08  

### Key Features
- ✅ .dctmp archive format support
- ✅ Docker permission handling
- ✅ Non-root container execution
- ✅ Automatic file permission correction

### Bug Fixes
- ✅ Fixed .dctmp files being copied instead of extracted
- ✅ Resolved Docker file permission issues
- ✅ Proper archive cleanup to finished directory

### Documentation
- ✅ Comprehensive Docker permission guide
- ✅ Updated README with new features
- ✅ Detailed release notes
- ✅ Migration instructions

## 🔍 Post-Release Tasks

### Testing
- [ ] Test Docker image with sample .dctmp files
- [ ] Verify file permissions in extracted folders
- [ ] Test non-root user execution
- [ ] Validate archive cleanup process

### Monitoring
- [ ] Monitor GitHub issues for new problems
- [ ] Check Docker Hub/GHCR for successful image builds
- [ ] Verify release downloads and usage

### Communication
- [ ] Update any relevant documentation sites
- [ ] Notify users about Docker permission fixes
- [ ] Share release notes in relevant communities

## 📝 Notes

This release primarily addresses Docker deployment issues and adds support for a new archive format. The changes are backward compatible and should not affect existing installations.

The Docker permission fixes are particularly important for users running CineRipR in containerized environments, as they resolve the common issue of extracted files being read-only for normal users.
