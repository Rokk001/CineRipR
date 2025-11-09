# Release Notes - CineRipR 1.0.33

## Critical Fix: RAR Extraction with Official 7-Zip

This release fixes a **critical bug** where multi-volume RAR archives failed to extract with "Unsupported Method" errors.

### The Problem
- The Docker container used `p7zip-full` (Linux port of 7-Zip)
- `p7zip-full` does **not** support all RAR compression algorithms, especially RAR5 format
- Archives that extracted fine with Windows 7-Zip failed in Docker with:
  ```
  ERROR: Unsupported Method : filename.mkv
  ```

### The Solution
- Replaced `p7zip-full` with **official 7-Zip 24.09 Linux binary** from 7-zip.org
- Official 7-Zip supports all RAR formats and compression methods
- Maintains full compatibility with Windows 7-Zip

### Changes
- **Dockerfile**: Downloads and installs official 7-Zip binary
- Created `7z` symlink for compatibility
- Removed `p7zip-full` dependency

### Impact
- ✅ Multi-volume RAR archives now extract correctly
- ✅ RAR5 archives are now supported
- ✅ All compression methods are supported
- ✅ Consistent behavior between Windows and Docker

### Upgrade Instructions
1. Pull new Docker image:
   ```bash
   docker pull ghcr.io/rokk001/cineripr:1.0.33
   # or
   docker pull ghcr.io/rokk001/cineripr:latest
   ```

2. Restart container:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

3. Verify 7-Zip version:
   ```bash
   docker exec cineripr 7z
   ```
   Should show: `7-Zip 24.09 (x64)`

### Technical Details
The official 7-Zip binary is downloaded from:
- URL: https://www.7-zip.org/a/7z2409-linux-x64.tar.xz
- Version: 24.09
- Platform: Linux x64

The binary is installed to `/usr/local/bin/7zz` with a symlink at `/usr/local/bin/7z`.

### Testing
Tested with:
- ✅ Multi-volume RAR archives (92 volumes)
- ✅ RAR5 compressed archives
- ✅ Standard RAR archives
- ✅ Old-style `.rXX` volume format

All formats now extract successfully.

