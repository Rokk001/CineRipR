# CineRipR Build & Development Scripts

This directory contains helper scripts for building, testing, and releasing CineRipR.

## 📜 Available Scripts

### 🐳 build-docker.sh
Build Docker images for CineRipR.

```bash
# Build with version from pyproject.toml
./scripts/build-docker.sh

# Build with specific version
./scripts/build-docker.sh 2.0.0
```

**Features:**
- Automatically tags with version and `latest`
- Extracts version from `pyproject.toml` if not specified
- Optional image testing after build
- Cross-platform (Linux, macOS, Windows with Git Bash)

### 🧪 run-tests.sh
Run the test suite with various options.

```bash
# Run all tests
./scripts/run-tests.sh

# Run with coverage report
./scripts/run-tests.sh --coverage

# Verbose output
./scripts/run-tests.sh --verbose

# Quick tests only (skip slow tests)
./scripts/run-tests.sh --quick

# Combine options
./scripts/run-tests.sh --coverage --verbose
```

**Features:**
- Automatic pytest installation if missing
- Coverage report generation (HTML + terminal)
- Test filtering (quick tests only)
- Colored output

### 🚀 create-release.sh
Automated release creation script.

```bash
# Create a new release
./scripts/create-release.sh 2.0.0
```

**Features:**
- Version bump in `pyproject.toml`
- Git tag creation and pushing
- Optional Docker image build and push
- Validation checks:
  - Semantic versioning format
  - Current branch check
  - Uncommitted changes check
  - CHANGELOG.md entry check

**Process:**
1. Updates version in `pyproject.toml`
2. Commits changes
3. Creates and pushes git tag
4. Optionally builds and pushes Docker image
5. Provides next steps for GitHub release

## 🔧 Usage Requirements

### Linux/macOS
All scripts work out of the box on Unix-like systems.

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run directly
./scripts/build-docker.sh
```

### Windows
Use Git Bash or WSL to run these scripts.

```bash
# In Git Bash
bash scripts/build-docker.sh

# Or in WSL
./scripts/build-docker.sh
```

## 📋 Prerequisites

- **Docker**: Required for `build-docker.sh`
- **Git**: Required for `create-release.sh`
- **Python 3.11+**: Required for `run-tests.sh`
- **pytest**: Automatically installed by `run-tests.sh` if missing

## 🎯 Common Workflows

### Development Cycle
```bash
# 1. Make changes to code
# 2. Run tests
./scripts/run-tests.sh --coverage

# 3. Build Docker image
./scripts/build-docker.sh

# 4. Test Docker image locally
docker run --rm cineripr:latest --version
```

### Release Process
```bash
# 1. Update CHANGELOG.md
# 2. Create release notes in docs/releases/
# 3. Run release script
./scripts/create-release.sh 2.0.0

# 4. Script will guide you through:
#    - Version bump
#    - Git tagging
#    - Docker build/push
```

### CI/CD Integration
These scripts can be used in GitHub Actions or other CI/CD systems:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: ./scripts/run-tests.sh --coverage

- name: Build Docker image
  run: ./scripts/build-docker.sh ${{ github.ref_name }}
```

## 🐛 Troubleshooting

### Permission Denied
```bash
chmod +x scripts/*.sh
```

### sed Command Not Found (Windows)
Install Git Bash or use WSL.

### Docker Build Fails
Check Docker daemon is running:
```bash
docker ps
```

### Tests Fail
Check Python version and dependencies:
```bash
python --version  # Should be 3.11+
pip install -e .  # Install package in development mode
```

## 🤝 Contributing

Feel free to add more helper scripts! Guidelines:
- Use bash for cross-platform compatibility
- Add clear usage documentation at the top
- Include error checking and validation
- Use colored output for readability
- Update this README with new scripts

See [Contributing Guide](../docs/development/contributing.md) for more details.

