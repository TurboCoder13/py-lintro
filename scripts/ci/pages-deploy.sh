#!/bin/bash
set -e

# GitHub Pages Deployment Script
# Handles the deployment of coverage reports to GitHub Pages

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [--help] [--badge-path PATH]"
    echo ""
    echo "GitHub Pages Deployment Script"
    echo "Handles the deployment of coverage reports to GitHub Pages."
    echo ""
    echo "Options:"
    echo "  --badge-path PATH   Optional path to coverage badge SVG to copy to _site/assets/images/coverage-badge.svg"
    echo ""
    echo "This script is designed to be run in GitHub Actions CI environment."
    echo "It prepares coverage reports for GitHub Pages deployment."
    exit 0
fi

BADGE_PATH=""
if [ "${1:-}" = "--badge-path" ] && [ -n "${2:-}" ]; then
    BADGE_PATH="$2"
fi

# Source shared utilities
source "$(dirname "$0")/../utils/utils.sh"

# Create coverage report directory
mkdir -p _site
cp -r coverage-report/* _site/
echo "<meta http-equiv=\"refresh\" content=\"0; url=index.html\">" > _site/index.html

# Optionally copy coverage badge
if [ -n "$BADGE_PATH" ] && [ -f "$BADGE_PATH" ]; then
    mkdir -p _site/assets/images
    cp "$BADGE_PATH" _site/assets/images/coverage-badge.svg || true
fi

log_success "GitHub Pages deployment files prepared in _site directory" 