#!/bin/bash

# Docker Build and Test Script
# Handles Docker image building and testing

# Source shared utilities
source "$(dirname "$0")/utils.sh"

log_info "Building Docker image..."
# Note: This script is designed to be used with the docker/build-push-action@v6
# The actual build is handled by the GitHub Action in the workflow
# This script focuses on testing the built image

log_info "Testing Docker image - List tools"
docker run --rm py-lintro:latest lintro list-tools

log_info "Testing Docker image - Version"
docker run --rm py-lintro:latest lintro --version

log_info "Testing Docker lintro script"
./scripts/docker-lintro.sh check .
