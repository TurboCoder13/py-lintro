#!/bin/bash

# lintro-docker.sh - Run lintro in a Docker container
# 
# This script allows running lintro without installing all the dependencies locally.
# It passes all arguments to the lintro command inside the Docker container.
#
# Usage:
#   ./lintro-docker.sh check --table-format --group-by code
#   ./lintro-docker.sh fmt --tools black,isort
#   ./lintro-docker.sh list-tools

set -e

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

# Build the Docker image if it doesn't exist
if ! docker image inspect lintro:latest &> /dev/null; then
    echo "Building Docker image..."
    docker build -t lintro:latest .
fi

# Run lintro in Docker with the current directory mounted
docker run --rm -v "$(pwd):/code" -w /code lintro:latest "$@"

# Exit with the same status code as the Docker command
exit $? 