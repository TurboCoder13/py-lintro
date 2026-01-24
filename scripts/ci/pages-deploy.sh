#!/usr/bin/env bash
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
# shellcheck source=../utils/utils.sh disable=SC1091 # Can't follow dynamic path; verified at runtime
source "$(dirname "$0")/../utils/utils.sh"

# Create coverage report directory
mkdir -p _site

# Detect layout of downloaded artifact and copy accordingly
if [ -f "coverage-report/index.html" ]; then
	cp -r coverage-report/* _site/
	REDIRECT_TARGET="index.html"
elif [ -f "coverage-report/htmlcov/index.html" ]; then
	cp -r coverage-report/htmlcov/* _site/
	REDIRECT_TARGET="index.html"
else
	# Fallback: copy all and point to a likely path
	cp -r coverage-report/* _site/
	if [ -f "_site/index.html" ]; then
		REDIRECT_TARGET="index.html"
	else
		REDIRECT_TARGET="htmlcov/index.html"
	fi
fi

# Only create a redirect if index.html was not provided by the artifact
if [ ! -f "_site/index.html" ]; then
	echo "<meta http-equiv=\"refresh\" content=\"0; url=${REDIRECT_TARGET}\">" >_site/index.html
fi

# Optionally copy coverage badge
if [ -n "$BADGE_PATH" ] && [ -f "$BADGE_PATH" ]; then
	mkdir -p _site/assets/images
	cp "$BADGE_PATH" _site/assets/images/coverage-badge.svg || true
fi

log_success "GitHub Pages deployment files prepared in _site directory"
