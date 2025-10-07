# CineRipR

![CI](https://github.com/Rokk001/CineRipR/actions/workflows/ci.yml/badge.svg)

Utility for extracting multi-part archives downloaded for media libraries (Jellyfin/Plex) and keeping the finished folder tidy. The tool scans a download directory, extracts supported archives into a mirrored folder structure, and moves successfully processed source files into a finished archive area where old files can be purged automatically.

## Features
- **Multi-part archive support**: Understands multi-part archives (e.g. `*.part01.rar`, `*.r00`, `*.zip.001`) and processes each set only once.
- **Smart TV Show organization**: Automatically organizes TV shows into `ShowName/Season XX/` structure with proper flattening of episode directories.
- **Subfolder management**: Handles `Subs`, `Sample`, and other subfolders with configurable policies.
- **Progress tracking**: Real-time progress bars for extraction, copying, and moving operations with consistent color coding per release.
- **Demo mode**: Dry-run the workflow without touching the filesystem to preview changes.
- **Automatic cleanup**: Configurable automatic cleanup of the finished directory based on file age.
- **Comprehensive logging**: Structured logging with detailed progress indicators for all operations.
- **CLI overrides**: Override any configuration setting via command-line arguments.

## Requirements
- Python 3.11 or newer (Python 3.12 recommended).
- [7-Zip](https://www.7-zip.org/) (or compatible) available on `PATH` or configured explicitly for extracting RAR archives.

## Installation
```bash
pip install .
```
This installs the package with the console entry point `cineripr`.

For local development without installation, add the `src/` directory to `PYTHONPATH` or use `pip install -e .`.

## Configuration
Create a `cineripr.toml` file (a starter version is included in the repository). Adjust the paths, retention settings, and optional tool overrides to match your environment:

```toml
# cineripr.toml
[paths]
# Multiple download roots supported (repeat lines in CLI with --download-root):
download_roots = ["C:/Media/Download", "D:/Torrents"]
extracted_root = "C:/Media/Extracted"
finished_root = "C:/Media/Finished"

[options]
finished_retention_days = 15
enable_delete = false
demo_mode = false
repeat_forever = false
repeat_after_minutes = 0

[subfolders]
include_sample = false
include_sub = false
include_other = false

[tools]
seven_zip = "C:/Program Files/7-Zip/7z.exe"
```

The CLI allows you to override any of these values at runtime.

## Usage
```bash
cineripr --config C:/path/to/cineripr.toml
```

Common flags:
- `--demo/--no-demo` — toggle demo mode.
- `--enable-delete/--no-enable-delete` — control cleanup deletions.
- `--retention-days N` — override retention period.
- `--download-root` (repeatable), `--extracted-root`, `--finished-root` — override individual paths.
- `--seven-zip PATH` — point to a custom 7-Zip executable for RAR extraction.
- `--debug` — enable detailed directory processing logs (off by default).

Use `cineripr --help` to list all available options.

## Run in Docker

Build locally:
```bash
docker build -t ghcr.io/<user-or-org>/cineripr:1.0.0 .
```

Run with volumes (paths anpassen):
```bash
docker run --rm \
  -v /pfad/zu/downloads:/data/downloads:ro \
  -v /pfad/zu/extracted:/data/extracted \
  -v /pfad/zu/finished:/data/finished \
  -v /pfad/zu/cineripr.toml:/config/cineripr.toml:ro \
  ghcr.io/<user-or-org>/cineripr:1.0.0 \
  --config /config/cineripr.toml
```

Hinweise:
- In der TOML Container-Pfade verwenden (z. B. `/data/*`).
- 7-Zip ist vorinstalliert (`/usr/bin/7z`).

## TV Show Organization

The tool automatically detects TV shows and organizes them with normalized season folders:

**Input structure:**
```
Download/
  12.Monkeys.S01.German.DL.1080p.BluRay.x264-LIM/
    12.Monkeys.S01E01.German.DL.1080p.BluRay.x264-LIM/
      lim-12monkeys-s01e01-1080p.rar
      Subs/
        lim-12monkeys-s01e01-1080p-subs.rar
```

**Output structure:**
```
Extracted/
  TV-Shows/
    12 Monkeys/
      Season 01/
        12.Monkeys.S01E01.German.DL.1080p.BluRay.x264-LIM.mkv
        Subs/
          German.srt
          English.srt
```

The tool:
- Extracts the show name from the release directory
- Normalizes season folders to `Season XX` format (e.g., `Season 01`, `Season 02`)
- Flattens episode directories - content is extracted directly into the season folder
- Preserves subfolder structure (Subs, Sample) according to your policy settings

## Project Structure

The codebase is organized into focused, maintainable modules:

```
src/cineripr/
├── __init__.py              # Package version
├── archive_constants.py     # Constants and regex patterns
├── archive_detection.py     # Archive discovery and grouping
├── archive_extraction.py    # Extraction logic with 7-Zip support
├── path_utils.py            # TV show path organization
├── file_operations.py       # File/directory management
├── archives.py              # Main orchestration
├── cleanup.py               # Cleanup and retention logic
├── config.py                # Configuration management
├── progress.py              # Progress tracking and display
└── cli.py                   # Command-line interface

All modules live under the `cineripr/` namespace.
```

This modular architecture provides:
- **Clear separation of concerns**: Each module has a single, well-defined responsibility
- **Easy testing**: Focused modules with clear interfaces
- **Better maintainability**: Smaller files are easier to understand and modify
- **Improved collaboration**: Multiple developers can work on different modules

For detailed refactoring documentation, see [REFACTORING.md](REFACTORING.md).

## Development
Run formatting and static checks as needed (example commands shown with `uv`/`pip`):
```bash
pip install -e .[dev]
pytest
```

The repository includes a small unit-test suite covering configuration parsing. Extend it as you evolve the project.

## License
Released under the MIT License. See [LICENSE](LICENSE) for details.