# Release Notes - CineRipR 1.0.30

## Added
- **WebGUI**: New web-based dashboard for monitoring extraction status and progress
  - Accessible on port 8080 by default (configurable via `--webgui-port`)
  - Real-time status updates every 2 seconds
  - Live progress tracking for current extraction
  - Log viewer with last 50 log entries
  - Statistics dashboard (processed, failed, unsupported, deleted counts)
  - API endpoints: `/api/status` and `/api/health`
  - Start with `--webgui` flag

- **Multi-Volume RAR Validation**: Enhanced validation for multi-volume RAR archives
  - Checks if all required volumes are present before extraction
  - Prevents "Unsupported Method" errors when volumes are missing
  - Reads volume count from RAR header using 7-Zip
  - Clear error messages when volumes are missing

## Fixed
- Multi-volume RAR extraction now validates volume count before attempting extraction
- Prevents extraction failures when not all volumes are present

## Changed
- Added Flask dependency (>=3.0.0) for WebGUI functionality
- Dockerfile now exposes port 8080 for WebGUI access
- Code cleanup: removed unused imports and debug files

## Removed
- Debug scripts: `debug_extraction_issue.py`, `debug_move_issue.py`, `METADATA_INTEGRATION_EXAMPLE.py`
- Unused imports cleaned up across codebase

## Usage

### Starting with WebGUI
```bash
# Start with WebGUI on default port 8080
cineripr --webgui

# Custom port
cineripr --webgui --webgui-port 9000

# Custom host and port
cineripr --webgui --webgui-host 0.0.0.0 --webgui-port 8080
```

### Docker
```bash
# Expose WebGUI port
docker run -p 8080:8080 ... --webgui
```

### Access WebGUI
Open your browser and navigate to `http://localhost:8080` (or your configured host/port)

## Notes
- WebGUI runs in a separate thread and does not block the main processing
- Status updates are thread-safe and can be accessed concurrently
- All existing functionality remains unchanged when WebGUI is not enabled
- Multi-volume RAR validation only runs when not in demo mode

