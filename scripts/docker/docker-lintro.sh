#!/bin/bash
set -e

# docker-lintro.sh - Run lintro in a Docker container

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [--help] [lintro arguments...]"
    echo ""
    echo "Docker Lintro Runner"
    echo "Run Lintro in a Docker container without installing dependencies locally."
    echo ""
    echo "Features:"
    echo "  - Builds Docker image if not exists"
    echo "  - Mounts current directory to container"
    echo "  - Handles permission issues"
    echo "  - Delegates to local-lintro.sh inside container"
    echo ""
    echo "Examples:"
    echo "  $0 check"
    echo "  $0 check --tools ruff,prettier"
    echo "  $0 format --tools ruff"
    echo "  $0 list-tools"
    echo ""
    echo "This script allows running lintro without installing all dependencies locally."
    exit 0
fi
# 
# This script allows running lintro without installing all the dependencies locally.
# It delegates all the heavy lifting to local-lintro.sh inside the Docker container.
#
# Usage:
#   ./docker-lintro.sh check --tools hadolint,prettier [PATH]
#   ./docker-lintro.sh fmt --tools prettier [PATH]
#   ./docker-lintro.sh list-tools

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Docker Lintro Runner ===${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    exit 1
fi

# Build the Docker image if it doesn't exist
IMAGE_NAME="py-lintro:latest"
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    echo -e "${YELLOW}Building Docker image...${NC}"
    if ! docker build -t "$IMAGE_NAME" .; then
        echo -e "${RED}Error: Failed to build Docker image${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${GREEN}✓ Using existing Docker image${NC}"
fi

# Run lintro in Docker using the local-lintro.sh script
# We mount the current directory to /code and set UV_CACHE_DIR to avoid permission issues
echo -e "${BLUE}Running lintro in Docker container...${NC}"
echo -e "${YELLOW}Arguments: $*${NC}"

docker run --rm \
    --log-driver=local \
    -v "$(pwd):/app" \
    -w /app \
    -e UV_CACHE_DIR=/tmp/uv-cache \
    -e UV_VENV_CACHE_DIR=/tmp/uv-venv-cache \
    -e RUNNING_IN_DOCKER=1 \
    -e UV_PROJECT_ENVIRONMENT=/tmp/venv \
    -e UV_BUILD_CACHE_DIR=/tmp/uv-build-cache \
    -e UV_PROJECT_DIR=/app \
    --entrypoint="" \
    --user root \
    "$IMAGE_NAME" \
    /usr/local/bin/fix-permissions.sh /app/scripts/local/local-lintro.sh "$@"

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Docker lintro completed${NC}"
else
    echo -e "${RED}✗ Docker lintro failed with exit code $EXIT_CODE${NC}"
fi
exit $EXIT_CODE 