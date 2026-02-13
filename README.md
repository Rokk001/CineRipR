<div align="center">

# 🎬 CineRipR

**Intelligent Archive Extraction & Organization for Media Libraries**

[![CI Status](https://github.com/Rokk001/CineRipR/actions/workflows/ci.yml/badge.svg)](https://github.com/Rokk001/CineRipR/actions)
[![Docker Build](https://github.com/Rokk001/CineRipR/actions/workflows/docker-build.yml/badge.svg)](https://github.com/Rokk001/CineRipR/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://hub.docker.com)

[Features](#-features) • [Quick Start](#-quick-start) • [WebGUI](#-webgui) • [Documentation](#-documentation) • [Docker](#-docker)
 
---

</div>

## 🎯 What is CineRipR?

CineRipR is a **powerful automation tool** for managing downloaded media archives. It automatically extracts multi-part archives, organizes TV shows and movies into proper directory structures, and keeps your media library tidy with intelligent cleanup.

Perfect for **Plex, Jellyfin, Emby** users who download multi-part RAR/ZIP archives!

### 🎥 The Problem It Solves

Downloaded media often comes as:
- Multi-part RAR archives (`*.part01.rar`, `*.r00`, `*.r01`, ...)
- Split ZIP files (`*.zip.001`, `*.zip.002`, ...)
- Nested directory structures with samples, subs, and extras

**CineRipR automates everything:**
1. ✅ Detects and validates multi-part archives
2. ✅ Extracts with progress tracking
3. ✅ Organizes TV shows into `ShowName/Season XX/` structure
4. ✅ Moves processed archives to finished directory
5. ✅ Cleans up old files automatically
6. ✅ Monitors everything via beautiful WebGUI

---

## ✨ Features

### 🚀 Core Functionality

| Feature                          | Description                                                                           |
| -------------------------------- | ------------------------------------------------------------------------------------- |
| **🗜️ Multi-Part Archives**        | Full support for RAR5, split ZIPs, and multi-volume archives                          |
| **📺 Smart TV Show Organization** | Automatic detection and organization into `ShowName/Season XX/`                       |
| **🎬 Movie Organization**         | Proper naming and structure for movie collections                                     |
| **🎥 TMDB Integration**           | Auto-fetch metadata and NFO creation for movies (requires API Token)                  |
| **✅ File Completeness Check**    | Verifies files are fully downloaded before processing (configurable stability period) |
| **🔄 Real-Time Progress**         | Live progress bars with color-coded status                                            |
| **🐳 Docker-Ready**               | Production-tested Docker image with official 7-Zip binary                             |
| **⚙️ Configurable**               | WebGUI settings + CLI args + optional TOML config                                     |

### 🌐 WebGUI Dashboard

**NEW in v2.0!** Modern web-based monitoring interface:

| Feature                   | Description                                  |
| ------------------------- | -------------------------------------------- |
| **📊 Real-Time Status**    | Live processing status and progress tracking |
| **📋 Queue Management**    | View pending archives and processing queue   |
| **💾 System Health**       | Disk space, CPU, and memory monitoring       |
| **📝 Live Logs**           | Filterable, searchable log viewer            |
| **📅 History Timeline**    | Visual timeline of processed releases        |
| **🎨 Dark/Light Mode**     | Theme toggle with persistent preferences     |
| **🎮 Manual Controls**     | Pause/resume processing on demand            |
| **🔊 Toast Notifications** | Audio alerts for important events            |

### 🛡️ Production-Ready

- ✅ **Docker-optimized** with proper permission handling
- ✅ **RAR5 support** via official 7-Zip Linux binary
- ✅ **UNC path support** for Windows network shares
- ✅ **Automatic retries** for network file systems
- ✅ **Demo mode** for safe testing
- ✅ **Comprehensive logging** with structured output

---

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Pull the latest image
docker pull ghcr.io/rokk001/cineripr:latest

# Run with Docker Compose
curl -O https://raw.githubusercontent.com/Rokk001/CineRipR/main/examples/docker-compose.yml
docker-compose up -d

# Access WebGUI at http://localhost:8080
```

### Using pip

```bash
# Install
pip install cineripr

# Run with CLI args (no config file needed)
cineripr \
  --download-root /data/downloads \
  --extracted-root /data/extracted \
  --finished-root /data/finished

# Or use config file (optional)
cineripr --config cineripr.toml
```

---

## 🌐 WebGUI

**Access the dashboard:** Open http://localhost:8080 in your browser

### Overview Tab
![WebGUI Overview](https://via.placeholder.com/800x400?text=WebGUI+Overview+-+Coming+Soon)

- **Real-time statistics**: Processed, failed, deleted archives
- **Current operation**: Live progress for active extraction
- **Control panel**: Pause/resume processing

### Queue Tab
![WebGUI Queue](https://via.placeholder.com/800x400?text=WebGUI+Queue+-+Coming+Soon)

- **Processing queue**: See what's waiting
- **Release details**: Click any item for detailed view
- **Status indicators**: Color-coded status for each item

### System Health Tab
![WebGUI Health](https://via.placeholder.com/800x400?text=WebGUI+Health+-+Coming+Soon)

- **Disk space monitoring**: Downloads, extracted, finished paths
- **System resources**: CPU and memory usage
- **7-Zip version**: Installed archive tool version

### History Tab
![WebGUI History](https://via.placeholder.com/800x400?text=WebGUI+History+-+Coming+Soon)

- **Visual timeline**: All processed releases
- **Duration tracking**: See how long each took
- **Success/failure markers**: Quick overview of outcomes

---

## 📦 Installation

### Docker (Production)

```yaml
# docker-compose.yml
version: "3.8"
services:
  cineripr:
    image: ghcr.io/rokk001/cineripr:latest
    container_name: cineripr
    ports:
      - "8080:8080"
    volumes:
      - /path/to/downloads:/data/downloads
      - /path/to/extracted:/data/extracted
      - /path/to/finished:/data/finished
      - /path/to/appdata/cineripr:/config  # For settings database
    restart: unless-stopped
    user: "99:100"  # Adjust to your system
    entrypoint: ["/bin/sh", "-c"]
    command: ["umask 000 && exec python -m cineripr.cli --download-root /data/downloads --extracted-root /data/extracted --finished-root /data/finished"]
    
    # Optional: TMDB Integration for Movie NFOs
    environment:
      - CINERIPR_TMDB_API_TOKEN=your_tmdb_read_access_token
```

### Python (Development)

```bash
# Clone repository
git clone https://github.com/Rokk001/CineRipR.git
cd CineRipR

# Install in development mode
pip install -e .[dev]

# Copy example config
cp examples/cineripr.toml.example cineripr.toml

# Edit configuration
nano cineripr.toml

# Run
cineripr --config cineripr.toml
```

---

## ⚙️ Configuration

### Configuration Methods

CineRipR supports multiple configuration methods with priority order:

1. **WebGUI Settings** (Highest Priority) - Configure via WebGUI at http://localhost:8080
2. **CLI Arguments** - Override settings via command-line
3. **TOML File** (Optional) - Legacy configuration file
4. **Defaults** - Built-in default values

### Docker Deployment (Recommended)

**No TOML file required!** Configure paths via CLI args, all other settings via WebGUI:

```yaml
command: ["umask 000 && exec python -m cineripr.cli --download-root /data/downloads --extracted-root /data/extracted --finished-root /data/finished"]
volumes:
  - /path/to/appdata/cineripr:/config  # Settings database stored here
```

**Configure via WebGUI:**
- Open http://localhost:8080
- Go to **Settings** tab
- Configure all settings (scheduling, retention, subfolders, etc.)
- Settings are saved automatically in SQLite database

### TOML Configuration (Optional)

If you prefer TOML files, create `cineripr.toml`:

```toml
[paths]
download_roots = ["/data/downloads"]
extracted_root = "/data/extracted"
finished_root = "/data/finished"

[options]
finished_retention_days = 15
enable_delete = false
demo_mode = false

[subfolders]
include_sample = false
include_sub = true
include_other = false
```

### TMDB Integration (Movie Metadata)

To enable automatic NFO downloading for movies, add your TMDB API Token to your **Docker Compose** configuration.

**1. Docker Compose (Recommended)**
Add the `CINERIPR_TMDB_API_TOKEN` environment variable to your service definition. Here is a complete example:

```yaml
version: "3.8"
services:
  cineripr:
    image: ghcr.io/rokk001/cineripr:latest
    container_name: cineripr
    restart: unless-stopped
    ports:
      - "8080:8080"
    user: "99:100"
    
    # TMDB API Token
    environment:
      - CINERIPR_TMDB_API_TOKEN=your_tmdb_read_access_token
      
    volumes:
      - /path/to/downloads:/data/downloads
      - /path/to/extracted:/data/extracted
      - /path/to/finished:/data/finished
      - /path/to/movies:/data/movies  # Optional: Final destination for Movies
      - /path/to/tvshows:/data/tvshows # Optional: Final destination for TV Shows
      - /path/to/appdata/cineripr:/config
    command: ["umask 000 && exec python -m cineripr.cli --download-root /data/downloads --extracted-root /data/extracted --finished-root /data/finished --movie-root /data/movies --tvshow-root /data/tvshows"]
```

**2. Local Development (Optional)**
Only for local testing without Docker. Create `cineripr.local.toml` (gitignored):
```toml
[tmdb]
api_token = "your_token"
```

### CLI Arguments

Set paths via CLI args (required if no TOML file):

```bash
cineripr \
  --download-root /data/downloads \
  --extracted-root /data/extracted \
  --finished-root /data/finished \
  --retention-days 30 \
  --enable-delete \
  --webgui-port 9090
```

Full list: `cineripr --help`

---

## 🐳 Docker

### Pre-built Images

```bash
# Latest stable release
docker pull ghcr.io/rokk001/cineripr:latest

# Specific version
docker pull ghcr.io/rokk001/cineripr:2.0.0
```

### Building Locally

```bash
# Using provided script
./scripts/build-docker.sh 2.0.0

# Or manually
docker build -t cineripr:2.0.0 .
```

### Docker Compose

See [examples/docker-compose.yml](examples/docker-compose.yml) for production-ready configuration.

**Key Features:**
- ✅ Official 7-Zip binary (full RAR5 support)
- ✅ Automatic permission handling
- ✅ Health checks
- ✅ Log rotation
- ✅ WebGUI on port 8080

---

## 📖 Documentation

### Quick Links

| Document                                                        | Description                  |
| --------------------------------------------------------------- | ---------------------------- |
| [Architecture Overview](docs/architecture/overview.md)          | System design and components |
| [Finished Path Logic](docs/architecture/finished-path-logic.md) | How file organization works  |
| [Contributing Guide](docs/development/contributing.md)          | How to contribute            |
| [Docker Permissions](docs/operations/docker-permissions.md)     | Docker setup guide           |
| [Release Notes](docs/releases/)                                 | All version histories        |

### Examples

- [Example Config](examples/cineripr.toml.example) - Full configuration file with comments
- [Docker Compose](examples/docker-compose.yml) - Production-ready Docker setup

### Scripts

- [Build Docker](scripts/build-docker.sh) - Build Docker images
- [Run Tests](scripts/run-tests.sh) - Execute test suite
- [Create Release](scripts/create-release.sh) - Automated release process

---

## 🔧 Development

### Setup

```bash
# Clone and install
git clone https://github.com/Rokk001/CineRipR.git
cd CineRipR
pip install -e .[dev]

# Run tests
./scripts/run-tests.sh --coverage

# Build Docker
./scripts/build-docker.sh
```

### Project Structure

```
CineRipR/
├── docs/              # Documentation
│   ├── architecture/  # Design docs
│   ├── development/   # Dev guides
│   ├── operations/    # Ops guides
│   └── releases/      # Release notes
├── examples/          # Example configs
├── scripts/           # Build scripts
├── src/cineripr/      # Source code
│   ├── core/         # Core logic
│   ├── extraction/   # Archive handling
│   ├── web/          # WebGUI
│   ├── cli.py        # CLI interface
│   ├── config.py     # Configuration
│   └── progress.py   # Progress tracking
└── tests/            # Test suite
    ├── unit/         # Unit tests
    └── integration/  # Integration tests
```

### Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src/cineripr --cov-report=html

# Specific test file
pytest tests/unit/test_config.py

# Verbose output
pytest -v
```

### Code Quality

- **Linting**: `ruff check src/`
- **Formatting**: `ruff format src/`
- **Type Checking**: `mypy src/`

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/development/contributing.md) for details.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`./scripts/run-tests.sh`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow existing code style
- Add tests for new features
- Update documentation
- Keep commits atomic and descriptive

---

## 📊 Release History

### Latest Releases

- **[v2.0.0](docs/releases/v2.0.0.md)** - Major restructuring and modernization
- **[v1.0.37](docs/releases/v1.0.37.md)** - Critical 7-Zip detection fix
- **[v1.0.36](docs/releases/v1.0.36.md)** - Complete WebGUI feature set
- **[v1.0.35](docs/releases/v1.0.35.md)** - Major WebGUI overhaul

See [CHANGELOG.md](CHANGELOG.md) for complete history.

---

## 🐛 Troubleshooting

### Common Issues

**Q: Archives fail to extract in Docker**
- Ensure 7-Zip is properly installed (should auto-detect `/usr/local/bin/7z`)
- Check Docker logs: `docker logs cineripr`

**Q: Permission errors on extracted files**
- Use `user: "99:100"` in Docker Compose (adjust to your system)
- Use `umask 000` in entrypoint for full permissions

**Q: WebGUI not accessible**
- Check port mapping: `-p 8080:8080`
- Verify container is running: `docker ps`
- Check firewall rules

**Q: TV shows not organizing correctly**
- Ensure release names follow standard patterns (Show.Name.S01E01)
- Enable debug logging: `--debug`
- Check [Finished Path Logic](docs/architecture/finished-path-logic.md)

For more help, see [Documentation](docs/) or open an [Issue](https://github.com/Rokk001/CineRipR/issues).

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌟 Acknowledgments

- **7-Zip** - Excellent archive tool with RAR5 support
- **Flask** - WebGUI framework
- **psutil** - System monitoring
- All contributors and users who provided feedback!

---

## 📞 Support & Community

- **Issues**: [GitHub Issues](https://github.com/Rokk001/CineRipR/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Rokk001/CineRipR/discussions)
- **Documentation**: [docs/](docs/)

---

<div align="center">

**Made with ❤️ for the media library community**

[⬆ Back to Top](#-cineripr)

</div>
