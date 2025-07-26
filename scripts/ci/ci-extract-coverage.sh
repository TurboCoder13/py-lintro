#!/bin/bash

# CI Coverage Extraction Script
# Handles extracting coverage percentage for CI pipeline

set -e

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [--help]"
    echo ""
    echo "CI Coverage Extraction Script"
    echo "Handles extracting coverage percentage for CI pipeline."
    echo ""
    echo "This script:"
    echo "  - Extracts coverage percentage from coverage.xml"
    echo "  - Sets COVERAGE_PERCENTAGE environment variable"
    echo "  - Handles missing coverage.xml gracefully"
    echo ""
    echo "This script is designed to be run in GitHub Actions CI environment."
    exit 0
fi

# Source shared utilities
source "$(dirname "$0")/../utils/utils.sh"

# Set up environment if not in GitHub Actions
GITHUB_ENV="${GITHUB_ENV:-/dev/null}"

log_info "Extracting coverage percentage from coverage.xml"

# Extract coverage percentage from coverage.xml
if [ -f coverage.xml ]; then
    # Run the Python script and capture only the percentage line
    python3 scripts/utils/extract-coverage.py | grep "^percentage=" > coverage-env.txt
    source coverage-env.txt
    echo "COVERAGE_PERCENTAGE=$percentage" >> $GITHUB_ENV
    log_success "Coverage extracted: $percentage%"
else
    echo "COVERAGE_PERCENTAGE=0.0" >> $GITHUB_ENV
    log_warning "No coverage.xml found, setting coverage to 0.0%"
fi 