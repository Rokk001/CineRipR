# Release Notes - CineRipR v1.0.37

**Release Date:** November 9, 2025

## 🐛 Critical Bug Fix Release

This release fixes a **critical issue** that prevented 7-Zip from being detected in Docker containers, causing RAR archive extraction to fail with "No such file or directory" errors.

---

## 🔧 Critical Fix

### 7-Zip Detection Enhancement

**Problem:** Docker containers running CineRipR were unable to extract RAR archives because 7-Zip was not being detected, even though it was installed.

**Root Cause:** The official 7-Zip Linux binary is installed in `/usr/local/bin/7z`, but the auto-detection logic only used `shutil.which()`, which depends on the user's `$PATH` environment variable. In Docker containers running as non-root user, `/usr/local/bin` might not be in the `$PATH`.

**Solution:** Enhanced `resolve_seven_zip_command()` to:
1. First try auto-detection via `$PATH` (existing behavior)
2. **NEW:** Fallback to explicit path checking for common installation locations:
   - `/usr/local/bin/7z` (official 7-Zip symlink)
   - `/usr/local/bin/7zz` (official 7-Zip main executable)
   - `/usr/bin/7z` (p7zip-full package)
   - `/usr/bin/7za` (p7zip package)
   - `/usr/bin/7zr` (p7zip package)

**Impact:** Multi-volume RAR archives (like `mhd-goonies.rar` with 92 parts) can now be extracted successfully in Docker containers.

---

## ✨ Additional Improvements

### WebGUI Enhancements

- **GitHub Link in Footer**: Added clickable GitHub repository link with icon
- **Hover Effect**: Enhanced footer link styling with smooth hover transition
- **Better Accessibility**: Link opens in new tab with proper security attributes

---

## 📦 What's Included

All features from v1.0.36 plus this critical fix:

### Core Features
- Multi-volume RAR archive extraction (RAR5 support)
- Automatic archive detection and processing
- TV Show and Movie organization
- Docker-friendly file operations

### WebGUI Features (from v1.0.36)
- Release Detail View with modal dialog
- Timeline/History View
- Manual Control Panel (pause/resume)
- Dark/Light Mode Toggle
- CPU & Memory Monitoring
- Toast Sound Notifications
- Log Filtering & Search
- System Health Dashboard

---

## 🚀 Upgrade Instructions

### Docker Users (Recommended)

```bash
docker pull ghcr.io/rokk001/cineripr:1.0.37
# or
docker pull ghcr.io/rokk001/cineripr:latest
```

Then restart your container. **This fix is especially important for Docker users!**

### pip Users

```bash
pip install --upgrade cineripr
```

---

## 🧪 Testing

This release was tested with:
- Multi-volume RAR archives (92 parts)
- Official 7-Zip 24.09 Linux binary
- Docker container with non-root user (UID 1000)
- RAR5 format archives

---

## 📝 Technical Details

### Modified Files
- `src/cineripr/archive_extraction.py`: Enhanced `resolve_seven_zip_command()`
- `src/cineripr/webgui.py`: Added GitHub footer link

### Code Changes
```python
# Before: Only checked PATH
for name in ("7z", "7za", "7zr"):
    resolved = shutil.which(name)
    if resolved:
        return resolved

# After: PATH check + explicit fallback
for name in ("7z", "7za", "7zr", "7zz"):
    resolved = shutil.which(name)
    if resolved:
        return resolved

# NEW: Fallback to common paths
common_paths = [
    "/usr/local/bin/7z",
    "/usr/local/bin/7zz",
    "/usr/bin/7z",
    # ... more paths
]
for path_str in common_paths:
    if Path(path_str).exists():
        return str(path_str)
```

---

## 🐛 Bug Reports

If you still experience issues with 7-Zip detection, please report:
- Your Docker/system setup
- Output of `which 7z` and `which 7zz`
- Contents of `$PATH` environment variable
- CineRipR logs with `--debug` flag

GitHub Issues: https://github.com/Rokk001/CineRipR/issues

---

## 🙏 Special Thanks

Thanks to users who reported the RAR extraction issue and helped identify the Docker PATH problem!

---

**Full Changelog**: https://github.com/Rokk001/CineRipR/blob/main/CHANGELOG.md

