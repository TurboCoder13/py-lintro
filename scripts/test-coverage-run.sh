#!/bin/bash

# Test Coverage Run Script
# Handles the comprehensive test suite execution in Docker

# Source shared utilities
source "$(dirname "$0")/utils.sh"

log_info "Building Docker image with all testing tools pre-installed"
docker compose build test-integration

log_info "Running comprehensive test suite with Python 3.13 in Docker"
log_info "All required tools are pre-installed:"
log_info "prettier, hadolint, ruff, darglint, yamllint"
docker compose run --rm test-integration
log_success "Coverage files should now be available in the current directory"

# Debug: Check what files are available after Docker run
log_info "Files in current directory after Docker run:"
ls -la

# Additional debugging for coverage files
log_info "Checking for coverage files specifically:"
if [ -f "coverage.xml" ]; then
    log_success "coverage.xml found (size: $(wc -c < coverage.xml) bytes)"
else
    log_warning "coverage.xml not found"
fi

if [ -d "htmlcov" ]; then
    log_success "htmlcov directory found"
    ls -la htmlcov/ | head -5
else
    log_warning "htmlcov directory not found"
fi

# Check if coverage files exist using shared functions
check_file_exists "coverage.xml" "coverage.xml"
check_dir_exists "htmlcov" "htmlcov directory" 