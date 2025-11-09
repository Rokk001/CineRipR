#!/bin/bash
#
# Build and tag CineRipR Docker image
#
# Usage:
#   ./scripts/build-docker.sh [VERSION]
#
# Example:
#   ./scripts/build-docker.sh 2.0.0
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="ghcr.io/rokk001/cineripr"
DOCKERFILE="Dockerfile"

# Get version from argument or pyproject.toml
if [ -n "$1" ]; then
    VERSION="$1"
else
    # Extract version from pyproject.toml
    VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
fi

if [ -z "$VERSION" ]; then
    echo -e "${RED}Error: Could not determine version${NC}"
    echo "Usage: $0 [VERSION]"
    exit 1
fi

echo -e "${GREEN}Building CineRipR Docker image${NC}"
echo "Version: $VERSION"
echo "Image: $IMAGE_NAME"
echo ""

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE" ]; then
    echo -e "${RED}Error: $DOCKERFILE not found${NC}"
    exit 1
fi

# Build image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t "${IMAGE_NAME}:${VERSION}" -t "${IMAGE_NAME}:latest" .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
    echo ""
    echo "Images created:"
    echo "  ${IMAGE_NAME}:${VERSION}"
    echo "  ${IMAGE_NAME}:latest"
    echo ""
    echo "To push to registry:"
    echo "  docker push ${IMAGE_NAME}:${VERSION}"
    echo "  docker push ${IMAGE_NAME}:latest"
else
    echo -e "${RED}✗ Docker build failed${NC}"
    exit 1
fi

# Optional: Test the image
echo ""
read -p "Test the image? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Testing Docker image...${NC}"
    docker run --rm "${IMAGE_NAME}:${VERSION}" --version
fi

echo -e "${GREEN}Done!${NC}"

