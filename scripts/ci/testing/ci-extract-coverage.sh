#!/bin/bash

# CI Coverage Extraction Script
# Handles extracting coverage percentage for CI pipeline

# Note: We don't use set -e here to handle edge cases gracefully
# The script should always succeed but may report 0.0% coverage

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
source "$(dirname "$0")/../../utils/utils.sh"

# Set up environment if not in GitHub Actions
GITHUB_ENV="${GITHUB_ENV:-/dev/null}"
GITHUB_OUTPUT="${GITHUB_OUTPUT:-/dev/null}"

# Helper function to set coverage percentage
set_coverage() {
    local pct="$1"
    echo "COVERAGE_PERCENTAGE=$pct" >> "$GITHUB_ENV"
    echo "percentage=$pct" >> "$GITHUB_OUTPUT"
}

log_info "Extracting coverage percentage from coverage.xml"

# Debug: Show what files exist
log_info "Checking for coverage files in $(pwd)..."
if [ -f coverage.xml ]; then
    log_info "coverage.xml exists ($(wc -c < coverage.xml) bytes)"
else
    log_warning "coverage.xml does not exist"
fi
if [ -f .coverage ]; then
    log_info ".coverage exists ($(wc -c < .coverage) bytes)"
else
    log_warning ".coverage does not exist"
fi

# Extract coverage percentage from coverage.xml
if [ -f coverage.xml ] && [ -s coverage.xml ]; then
    # File exists and is not empty
    log_info "Attempting to extract coverage from coverage.xml..."
    
    # Clean up .venv if it exists and might have permission issues from Docker
    # Docker may create .venv as root, causing uv run to fail
    # Try to remove it (will fail silently if we don't have permissions)
    if [ -d .venv ]; then
        log_info "Cleaning up .venv directory (may have permission issues from Docker)..."
        rm -rf .venv 2>/dev/null || true
    fi
    
    # Try to run the Python script with uv run first
    # If that fails due to venv issues, fall back to python3 directly
    output=""
    if output=$(uv run python scripts/utils/extract-coverage.py 2>&1); then
        # Extract percentage from output
        if percentage_line=$(echo "$output" | grep "^percentage="); then
            percentage="${percentage_line#percentage=}"
            set_coverage "$percentage"
            log_success "Coverage extracted: $percentage%"
            exit 0
        else
            log_warning "Python script ran but no percentage found in output"
            log_warning "Output was: $output"
        fi
    else
        log_warning "Failed to run coverage extraction script with uv run"
        log_warning "Error: $output"
        log_info "Attempting fallback with python3 directly..."
        # Fallback: use python3 directly (script has stdlib fallback if defusedxml unavailable)
        if output=$(python3 scripts/utils/extract-coverage.py 2>&1); then
            if percentage_line=$(echo "$output" | grep "^percentage="); then
                percentage="${percentage_line#percentage=}"
                set_coverage "$percentage"
                log_success "Coverage extracted via python3 fallback: $percentage%"
                exit 0
            fi
        fi
    fi
    
    # Fallback: try to extract directly from XML
    log_info "Attempting fallback XML extraction..."
    if line_rate=$(grep -o 'line-rate="[^"]*"' coverage.xml | head -1 | cut -d'"' -f2); then
        if [ -n "$line_rate" ] && [ "$line_rate" != "0" ]; then
            # Convert line rate (0.XX) to percentage
            percentage=$(echo "$line_rate * 100" | bc -l 2>/dev/null | cut -d'.' -f1)
            if [ -n "$percentage" ]; then
                set_coverage "${percentage}.0"
                log_success "Coverage extracted via fallback: ${percentage}%"
                exit 0
            fi
        fi
    fi
fi

# No coverage found - set to 0.0%
set_coverage "0.0"
log_warning "No valid coverage data found, setting coverage to 0.0%"
exit 0 