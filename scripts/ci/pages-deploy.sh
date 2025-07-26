#!/bin/bash

# GitHub Pages Deployment Script
# Handles the deployment of coverage reports to GitHub Pages

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [--help]"
    echo ""
    echo "GitHub Pages Deployment Script"
    echo "Handles the deployment of coverage reports to GitHub Pages."
    echo ""
    echo "This script is designed to be run in GitHub Actions CI environment."
    echo "It prepares coverage reports for GitHub Pages deployment."
    exit 0
fi

# Source shared utilities
source "$(dirname "$0")/../utils/utils.sh"

# Create coverage report directory
mkdir -p _site
cp -r coverage-report/* _site/
echo "<meta http-equiv=\"refresh\" content=\"0; url=index.html\">" > _site/index.html

log_success "GitHub Pages deployment files prepared in _site directory" 