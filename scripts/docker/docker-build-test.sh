#!/usr/bin/env bash

# Docker Build and Test Script
# Handles Docker image building and testing

set -euo pipefail

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
	echo "Usage: $0 [--help]"
	echo ""
	echo "Docker Build and Test Script"
	echo "Handles Docker image building and testing."
	echo ""
	echo "This script tests the Docker image by:"
	echo "  - Listing available tools"
	echo "  - Checking version information"
	echo "  - Running lintro in Docker container"
	echo ""
	echo "This script is designed to be used with GitHub Actions."
	exit 0
fi

# Source shared utilities
# shellcheck source=../utils/utils.sh disable=SC1091 # Can't follow dynamic path; verified at runtime
source "$(dirname "$0")/../utils/utils.sh"

log_info "Building Docker image..."
# Note: This script is designed to be used with the docker/build-push-action@v6
# The actual build is handled by the GitHub Action in the workflow
# This script focuses on testing the built image

log_info "Testing Docker image - List tools"
docker run --rm py-lintro:latest lintro list-tools

log_info "Testing Docker image - Version"
docker run --rm py-lintro:latest lintro --version

log_info "Testing Docker lintro script"
# Note: darglint timeout increased for CI (Docker is slower than local)
./scripts/docker/docker-lintro.sh check . --tool-options darglint:timeout=180
