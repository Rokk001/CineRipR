# Emby Extractor

Utility for extracting multi-part archives downloaded for Emby (or any media server) and keeping the finished folder tidy. The tool scans a download directory, extracts supported archives into a mirrored folder structure, and moves successfully processed source files into a finished archive area where old files can be purged automatically.

## Features
- Understands multi-part archives (e.g. `*.part01.rar`, `*.r00`, `*.zip.001`) and processes each set only once.
- Optional demo mode to dry-run the workflow without touching the filesystem.
- Configurable automatic cleanup of the finished directory based on file age.
- CLI overrides for every runtime setting and structured logging with progress indicators.

## Requirements
- Python 3.11 or newer (Python 3.12 recommended).
- [7-Zip](https://www.7-zip.org/) (or compatible) available on `PATH` or configured explicitly for extracting RAR archives.

## Installation
```bash
pip install .
```
This installs the package with the console entry point named `emby-extractor`.

For local development without installation, add the `src/` directory to `PYTHONPATH` or use `pip install -e .`.

## Configuration
Create an `emby_extractor.toml` file (a starter version is included in the repository). Adjust the paths, retention settings, and optional tool overrides to match your environment:

```toml
# emby_extractor.toml
[paths]
download_root = "C:/Media/Download"
extracted_root = "C:/Media/Extracted"
finished_root = "C:/Media/Finished"

[options]
finished_retention_days = 14
enable_delete = false
demo_mode = false

[tools]
seven_zip = "C:/Program Files/7-Zip/7z.exe"
```

The CLI allows you to override any of these values at runtime.

## Usage
```bash
emby-extractor --config C:/path/to/emby_extractor.toml
```

Common flags:
- `--demo/--no-demo` — toggle demo mode.
- `--enable-delete/--no-enable-delete` — control cleanup deletions.
- `--retention-days N` — override retention period.
- `--download-root`, `--extracted-root`, `--finished-root` — override individual paths.
- `--seven-zip PATH` — point to a custom 7-Zip executable for RAR extraction.

Use `emby-extractor --help` to list all available options.

## Development
Run formatting and static checks as needed (example commands shown with `uv`/`pip`):
```bash
pip install -e .[dev]
pytest
```

The repository includes a small unit-test suite covering configuration parsing. Extend it as you evolve the project.

## License
Released under the MIT License. See [LICENSE](LICENSE) for details.