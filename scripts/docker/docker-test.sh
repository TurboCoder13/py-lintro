#!/bin/bash
set -e

# docker-test.sh - Run tests in a Docker container

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [--help]"
    echo ""
    echo "Docker Integration Test Runner"
    echo "Run integration tests in Docker container with all tools pre-installed."
    echo ""
    echo "Features:"
    echo "  - Uses Docker Compose for test environment"
    echo "  - All tools pre-installed in container"
    echo "  - Delegates to run-tests.sh inside container"
    echo "  - Provides clear success/failure output"
    echo ""
    echo "This script runs the full test suite in a containerized environment."
    exit 0
fi
# 
# This script runs the full test suite in a containerized environment
# where all tools are pre-installed. It delegates to run-tests.sh inside the container.

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Docker Integration Test Runner ===${NC}"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Use Docker Compose v2 (standard)
DOCKER_COMPOSE_CMD="docker compose"
echo -e "${GREEN}Using Docker Compose v2${NC}"

IMAGE_NAME="py-lintro-test:latest"

# Check if we need to build the Docker image
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    echo -e "${YELLOW}Building Docker image...${NC}"
    $DOCKER_COMPOSE_CMD build test-integration
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${GREEN}✓ Using existing Docker image${NC}"
fi

# Run the integration tests in Docker using run-tests.sh
echo -e "${BLUE}Running integration tests in Docker...${NC}"
echo -e "${YELLOW}All tools are pre-installed in the Docker environment${NC}"

if $DOCKER_COMPOSE_CMD run --rm test-integration; then
    echo -e "${GREEN}=== All tests passed! ===${NC}"
    exit 0
else
    echo -e "${RED}=== Tests failed! ===${NC}"
    exit 1
fi
   