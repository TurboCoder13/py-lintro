#!/usr/bin/env bash
set -euo pipefail

# Coverage Badge Update Script
# Generates and updates the coverage badge

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../utils/utils.sh
source "$SCRIPT_DIR/../../utils/utils.sh"

# Show help if requested
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    cat <<'EOF'
Usage: coverage-badge-update.sh [--help]

Coverage Badge Update Script
Generates and updates the coverage badge.

This script:
  - Extracts coverage percentage from coverage.xml
  - Generates SVG badge with appropriate color
  - Updates assets/images/coverage-badge.svg file
  - Commits changes in CI environment

This script is designed to be run in GitHub Actions CI environment.
EOF
    exit 0
fi

# Set coverage percentage if not already set (handle nounset)
if [[ -z "${COVERAGE_PERCENTAGE:-}" ]]; then
    # Use shared get_coverage_percentage function from utils.sh
    COVERAGE_PERCENTAGE=$(get_coverage_percentage "coverage.xml")
    if [[ "$COVERAGE_PERCENTAGE" != "0.00" ]]; then
        log_info "Extracted coverage percentage: $COVERAGE_PERCENTAGE%"
    else
        log_warning "No coverage.xml found or empty, setting coverage to 0.0%"
        COVERAGE_PERCENTAGE="0.0"
    fi
fi

# Generate badge based on coverage percentage
if [ -f "coverage.xml" ]; then
    log_info "Generating coverage badge with $COVERAGE_PERCENTAGE% coverage..."
    
    # Determine color based on coverage percentage
    if (( $(echo "$COVERAGE_PERCENTAGE >= 80" | bc -l) )); then
        color="#4c1"  # Green
    elif (( $(echo "$COVERAGE_PERCENTAGE >= 60" | bc -l) )); then
        color="#dfb317"  # Yellow
    else
        color="#e05d44"  # Red
    fi
    
    # Create SVG badge with actual coverage percentage
    cat > assets/images/coverage-badge.svg << EOF
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="99" height="20">
    <linearGradient id="b" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linearGradient>
    <clipPath id="a">
        <rect width="99" height="20" rx="3" fill="#fff"/>
    </clipPath>
    <g clip-path="url(#a)">
        <path fill="#555" d="M0 0h63v20H0z"/>
        <path fill="$color" d="M63 0h36v20H63z"/>
        <path fill="url(#b)" d="M0 0h99v20H0z"/>
    </g>
    <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="110">
        <text x="325" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="530">coverage</text>
        <text x="325" y="140" transform="scale(.1)" textLength="530">coverage</text>
        <text x="800" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="260">${COVERAGE_PERCENTAGE}%</text>
        <text x="800" y="140" transform="scale(.1)" textLength="260">${COVERAGE_PERCENTAGE}%</text>
    </g>
</svg>
EOF
    log_success "Generated coverage badge with $COVERAGE_PERCENTAGE% coverage"
else
    log_warning "No coverage.xml found, creating default badge"
    COVERAGE_PERCENTAGE="0.0"
    cat > assets/images/coverage-badge.svg << EOF
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="99" height="20">
    <linearGradient id="b" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linearGradient>
    <clipPath id="a">
        <rect width="99" height="20" rx="3" fill="#fff"/>
    </clipPath>
    <g clip-path="url(#a)">
        <path fill="#555" d="M0 0h63v20H0z"/>
        <path fill="#e05d44" d="M63 0h36v20H63z"/>
        <path fill="url(#b)" d="M0 0h99v20H0z"/>
    </g>
    <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="110">
        <text x="325" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="530">coverage</text>
        <text x="325" y="140" transform="scale(.1)" textLength="530">coverage</text>
        <text x="800" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="260">0%</text>
        <text x="800" y="140" transform="scale(.1)" textLength="260">0%</text>
    </g>
</svg>
EOF
    log_info "Created default badge with 0% coverage"
fi

# Update badge locally or in CI
if [ -n "${CI:-}" ] || [ -n "${GITHUB_ACTIONS:-}" ]; then
    # Default: do not push from CI to keep runs idempotent
    if [ "${COVERAGE_BADGE_COMMIT:-false}" = "true" ]; then
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add assets/images/coverage-badge.svg
        if ! git diff --quiet --cached; then
            git commit -m "docs: update coverage badge - $COVERAGE_PERCENTAGE%"
            git push
            log_success "Coverage badge updated and pushed to repository"
        else
            log_info "Coverage badge unchanged, no commit needed"
        fi
    else
        log_info "CI detected; skipping commit/push of coverage badge (set COVERAGE_BADGE_COMMIT=true to enable)"
    fi
else
    # Local: just update the badge file
    log_success "Coverage badge updated locally: assets/images/coverage-badge.svg"
    log_info "Current coverage: $COVERAGE_PERCENTAGE%"
fi