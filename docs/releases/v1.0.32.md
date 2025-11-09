# Release Notes - CineRipR 1.0.32

## Changed
- **WebGUI now enabled by default**: WebGUI starts automatically on port 8080
  - No need to specify `--webgui` flag anymore
  - Use `--no-webgui` to disable if needed
  - Improved error handling and logging for WebGUI startup

## Technical Details
- Changed `--webgui` from `action="store_true"` to `action=argparse.BooleanOptionalAction` with `default=True`
- Enhanced error messages for Flask import failures and port conflicts
- Better thread status checking to detect WebGUI startup issues

## Usage

### Default (WebGUI enabled)
```bash
cineripr --config cineripr.toml
# WebGUI automatically starts on port 8080
```

### Disable WebGUI
```bash
cineripr --config cineripr.toml --no-webgui
```

### Docker
No changes needed - WebGUI starts automatically:
```yaml
command: ["umask 000 && exec python -m cineripr.cli --config /config/cineripr.toml"]
# WebGUI will start automatically on port 8080
```

