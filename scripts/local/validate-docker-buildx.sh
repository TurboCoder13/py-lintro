#!/bin/bash

# Docker Buildx Configuration Validator
# Validates Docker Buildx driver and cache configuration locally
#
# Usage: ./scripts/local/validate-docker-buildx.sh [--help]
#
# This script is a diagnostic tool to validate that:
# - Docker Buildx is properly configured
# - The docker-container driver works with cache backends
# - The build process completes successfully
#
# This is NOT part of the regular test suite. Use it for:
# - Troubleshooting Docker build issues
# - Validating CI configuration changes locally
# - Debugging cache-related problems

set -euo pipefail

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo "Usage: $0 [--help]"
    echo ""
    echo "Docker Buildx Configuration Validator"
    echo "Validates Docker Buildx driver and cache configuration locally."
    echo ""
    echo "This script validates that:"
    echo "  - Docker Buildx is properly configured"
    echo "  - The docker-container driver works with cache backends"
    echo "  - The build process completes successfully"
    echo ""
    echo "This is a diagnostic tool for:"
    echo "  - Troubleshooting Docker build issues"
    echo "  - Validating CI configuration changes locally"
    echo "  - Debugging cache-related problems"
    echo ""
    echo "This is NOT part of the regular test suite."
    exit 0
fi

# Source shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../utils/utils.sh"

log_info "Validating Docker Buildx Configuration..."

# Check current buildx version
log_info "Checking Buildx version..."
docker buildx version

# Create a test builder with docker-container driver
log_info "Creating test builder with docker-container driver..."
docker buildx create --name test-builder --driver docker-container --use

# Inspect the builder
log_info "Inspecting builder configuration..."
docker buildx inspect test-builder

# Try building the image with cache
log_info "Building image with cache..."
docker buildx build \
  --platform linux/amd64 \
  --cache-from type=local,src=/tmp/buildx-cache \
  --cache-to type=local,dest=/tmp/buildx-cache,mode=max \
  --load \
  -t py-lintro:test \
  .

log_success "Build successful!"

# Cleanup
log_info "Cleaning up..."
docker buildx use default
docker buildx rm test-builder
rm -rf /tmp/buildx-cache

log_success "Validation completed successfully!"
log_info "Docker Buildx is properly configured for use with cache backends."
