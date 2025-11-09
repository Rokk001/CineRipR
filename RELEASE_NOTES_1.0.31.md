# Release Notes - CineRipR 1.0.31

## Fixed
- **WebGUI Connection Issues**: Fixed WebGUI not being accessible after processing completes
  - WebGUI now runs as non-daemon thread (prevents premature termination)
  - Main thread waits for WebGUI when active, keeping the server running
  - Fixes "ERR_CONNECTION_REFUSED" errors when accessing WebGUI

## Technical Details
- Changed WebGUI thread from `daemon=True` to `daemon=False`
- Added main thread wait loop when WebGUI is active and `repeat_forever` is disabled
- Added 1-second startup delay to ensure Flask server has time to initialize

## Usage
The WebGUI now remains accessible even after processing completes. Simply start with:
```bash
cineripr --webgui
```

The program will keep running and serving the WebGUI until you press Ctrl+C.

