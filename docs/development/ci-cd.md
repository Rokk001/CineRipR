# CI/CD Pipeline Documentation

## Overview

This project uses GitHub Actions for automated Docker image building and publishing. The CI/CD pipeline automatically builds and publishes Docker images to GitHub Container Registry (ghcr.io) whenever code is pushed or releases are created.

## Workflows

### 1. Docker Build Workflow (`.github/workflows/docker-build.yml`)

**Triggers:**
- Push to `main` branch
- Push of version tags (e.g., `v1.0.12`)
- Pull requests to `main` branch
- Manual trigger via GitHub UI

**Features:**
- Multi-platform builds (linux/amd64, linux/arm64)
- Automatic tagging based on branch/tag
- GitHub Container Registry publishing
- Build caching for faster builds
- Automatic `latest` tag for main branch

**Tags Generated:**
- `latest` - for main branch pushes
- `v1.0.12` - for version tags
- `v1.0` - for major.minor versions
- `v1` - for major versions
- Branch names for feature branches

### 2. Release Workflow (`.github/workflows/release.yml`)

**Triggers:**
- Push of version tags (e.g., `v1.0.12`)
- Manual trigger with custom tag input

**Features:**
- Release-specific builds
- Both version-specific and `latest` tags
- Multi-platform support
- Build optimization with caching

## Docker Images

### Registry Location
```
ghcr.io/rokk001/cineripr
```

### Available Tags
- `ghcr.io/rokk001/cineripr:latest` - Latest stable version
- `ghcr.io/rokk001/cineripr:1.0.12` - Specific version
- `ghcr.io/rokk001/cineripr:1.0` - Latest patch for minor version
- `ghcr.io/rokk001/cineripr:1` - Latest version for major version

### Multi-Platform Support
- **linux/amd64** - Intel/AMD 64-bit processors
- **linux/arm64** - ARM 64-bit processors (Apple Silicon, ARM servers)

## Usage

### Pull Latest Version
```bash
docker pull ghcr.io/rokk001/cineripr:latest
```

### Pull Specific Version
```bash
docker pull ghcr.io/rokk001/cineripr:1.0.12
```

### Run Container
```bash
docker run --rm \
  -v /path/to/downloads:/data/downloads:ro \
  -v /path/to/extracted:/data/extracted \
  -v /path/to/finished:/data/finished \
  -v /path/to/config.toml:/config/cineripr.toml:ro \
  ghcr.io/rokk001/cineripr:latest \
  --config /config/cineripr.toml
```

## Build Process

### Automatic Builds
1. **Code Push** → Build triggered automatically
2. **Tag Push** → Release build triggered
3. **Pull Request** → Build for testing (not published)

### Manual Builds
1. Go to GitHub Actions tab
2. Select "Release Build" workflow
3. Click "Run workflow"
4. Enter tag name (e.g., `v1.0.12`)
5. Click "Run workflow"

### Build Steps
1. Checkout repository
2. Set up Docker Buildx
3. Login to GitHub Container Registry
4. Extract metadata and generate tags
5. Build multi-platform image
6. Push to registry

## Permissions

### Required GitHub Permissions
- `contents: read` - Read repository content
- `packages: write` - Write to GitHub Container Registry

### Automatic Token
The workflow uses `${{ secrets.GITHUB_TOKEN }}` which is automatically provided by GitHub Actions.

## Monitoring

### Build Status
- Check GitHub Actions tab for build status
- Green checkmark = successful build
- Red X = failed build

### Image Availability
- Images are available immediately after successful build
- Check [GitHub Packages](https://github.com/Rokk001/CineRipR/pkgs/container/cineripr) for published images

## Troubleshooting

### Common Issues

1. **Build Fails**
   - Check GitHub Actions logs
   - Verify Dockerfile syntax
   - Ensure all dependencies are available

2. **Image Not Found**
   - Wait for build to complete
   - Check if image was published to correct registry
   - Verify tag name is correct

3. **Permission Denied**
   - Ensure repository has proper permissions
   - Check if GitHub token has required scopes

### Debug Commands
```bash
# Check available tags
docker search ghcr.io/rokk001/cineripr

# Inspect image
docker inspect ghcr.io/rokk001/cineripr:latest

# Check image platforms
docker buildx imagetools inspect ghcr.io/rokk001/cineripr:latest
```

## Benefits

### For Users
- **No local building required** - Pull pre-built images
- **Multi-platform support** - Works on different architectures
- **Automatic updates** - Latest images always available
- **Version pinning** - Use specific versions for stability

### For Developers
- **Automated builds** - No manual Docker building
- **Consistent environments** - Same build process every time
- **Easy releases** - Just push a tag to create release
- **Build caching** - Faster subsequent builds

## Security

### Image Security
- **Non-root user** - Container runs as `cineripr` user
- **Minimal base image** - Based on official Python image
- **Regular updates** - Base images updated regularly
- **No secrets in image** - All secrets handled via environment

### Registry Security
- **Private by default** - Images are private to organization
- **Access control** - Manage who can pull images
- **Vulnerability scanning** - GitHub scans for vulnerabilities
- **Signed images** - Images are signed for authenticity
