#!/bin/bash

# CineRipR Release 1.0.30 Creation Script
# This script creates a new release with proper tagging and documentation

set -e

VERSION="1.0.30"
TAG="v${VERSION}"
RELEASE_TITLE="CineRipR ${VERSION} - WebGUI & Multi-Volume RAR Validation"

echo "🚀 Creating CineRipR Release ${VERSION}"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check if working directory is clean
if ! git diff-index --quiet HEAD --; then
    echo "❌ Error: Working directory is not clean. Please commit or stash changes."
    exit 1
fi

# Check if tag already exists
if git rev-parse "${TAG}" > /dev/null 2>&1; then
    echo "❌ Error: Tag ${TAG} already exists"
    exit 1
fi

echo "✅ Pre-release checks passed"

# Create and push the tag
echo "📝 Creating tag ${TAG}..."
git tag -a "${TAG}" -m "Release ${VERSION}

${RELEASE_TITLE}

This release adds WebGUI support for status monitoring and improves multi-volume RAR validation.

Key Changes:
- Added WebGUI dashboard on port 8080 for real-time status monitoring
- Enhanced multi-volume RAR validation (checks for missing volumes)
- Added Flask dependency for WebGUI functionality
- Code cleanup: removed debug scripts and unused imports
- Dockerfile exposes port 8080 for WebGUI access

See RELEASE_NOTES_1.0.30.md for detailed information."

echo "📤 Pushing tag to remote..."
git push origin "${TAG}"

echo "🎉 Release ${VERSION} created successfully!"
echo ""
echo "Next steps:"
echo "1. Go to GitHub and create a release from tag ${TAG}"
echo "2. Copy content from RELEASE_NOTES_1.0.30.md for the release description"
echo "3. Build and push Docker image:"
echo "   docker build -t ghcr.io/rokk001/cineripr:${VERSION} ."
echo "   docker push ghcr.io/rokk001/cineripr:${VERSION}"
echo "4. Update latest tag:"
echo "   docker tag ghcr.io/rokk001/cineripr:${VERSION} ghcr.io/rokk001/cineripr:latest"
echo "   docker push ghcr.io/rokk001/cineripr:latest"
echo ""
echo "Release URL: https://github.com/Rokk001/CineRipR/releases/tag/${TAG}"

