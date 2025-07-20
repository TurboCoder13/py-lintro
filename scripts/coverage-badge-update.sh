#!/bin/bash

# Coverage Badge Update Script
# Generates and updates the coverage badge

# Source shared utilities
source "$(dirname "$0")/utils.sh"

# Generate badge from existing coverage data
uv run coverage-badge -o coverage-badge.svg -f
log_success "Generated coverage badge with current coverage percentage"

# Commit and push badge if changed
git config --local user.email "action@github.com"
git config --local user.name "GitHub Action"
git add coverage-badge.svg
git diff --quiet && git diff --staged --quiet || \
    git commit -m "docs: update coverage badge - $COVERAGE_PERCENTAGE%"
git push 