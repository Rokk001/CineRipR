#!/bin/bash
#
# Create a new CineRipR release
#
# This script automates the release process:
#   1. Updates version in pyproject.toml
#   2. Creates git tag
#   3. Pushes to GitHub
#   4. Optionally builds and pushes Docker image
#
# Usage:
#   ./scripts/create-release.sh VERSION
#
# Example:
#   ./scripts/create-release.sh 2.0.0
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}Error: Version argument required${NC}"
    echo "Usage: $0 VERSION"
    echo "Example: $0 2.0.0"
    exit 1
fi

VERSION="$1"

# Validate version format (semantic versioning)
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}Error: Invalid version format${NC}"
    echo "Version must be in format: MAJOR.MINOR.PATCH (e.g., 2.0.0)"
    exit 1
fi

echo -e "${GREEN}Creating CineRipR release v${VERSION}${NC}"
echo ""

# Check if we're on main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}Warning: Not on main branch (currently on: $CURRENT_BRANCH)${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 1
    fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}Error: Uncommitted changes detected${NC}"
    echo "Please commit or stash your changes first"
    exit 1
fi

# Update version in pyproject.toml
echo -e "${YELLOW}Updating version in pyproject.toml...${NC}"
sed -i "s/^version = \".*\"/version = \"${VERSION}\"/" pyproject.toml

# Check if CHANGELOG.md entry exists
if ! grep -q "## \[${VERSION}\]" CHANGELOG.md; then
    echo -e "${RED}Warning: No CHANGELOG.md entry found for v${VERSION}${NC}"
    read -p "Continue without changelog entry? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 1
    fi
fi

# Git operations
echo -e "${YELLOW}Creating git tag and pushing...${NC}"
git add pyproject.toml
git commit -m "Bump version to ${VERSION}"
git tag -a "v${VERSION}" -m "Release v${VERSION}"
git push origin main
git push origin "v${VERSION}"

echo -e "${GREEN}✓ Git release created${NC}"
echo ""

# Ask about Docker build
read -p "Build and push Docker image? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Building Docker image...${NC}"
    ./scripts/build-docker.sh "$VERSION"
    
    echo ""
    read -p "Push to registry? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker push "ghcr.io/rokk001/cineripr:${VERSION}"
        docker push "ghcr.io/rokk001/cineripr:latest"
        echo -e "${GREEN}✓ Docker images pushed${NC}"
    fi
fi

echo ""
echo -e "${GREEN}Release v${VERSION} created successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Create GitHub release at: https://github.com/Rokk001/CineRipR/releases/new"
echo "  2. Attach release notes from: docs/releases/v${VERSION}.md"
echo "  3. Announce the release"

