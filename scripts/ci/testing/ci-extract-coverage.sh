#!/usr/bin/env bash

# CI Coverage Extraction Script
# Handles extracting coverage percentage for CI pipeline
#
# Note: We use set -uo pipefail but not -e to handle edge cases gracefully.
# The script should always succeed but may report 0.0% coverage.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../utils/utils.sh disable=SC1091 # Can't follow dynamic path; verified at runtime
source "$SCRIPT_DIR/../../utils/utils.sh"

# Show help if requested
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Usage: ci-extract-coverage.sh [--help]

CI Coverage Extraction Script
Handles extracting coverage percentage for CI pipeline.

This script:
  - Extracts coverage percentage from coverage.xml
  - Sets COVERAGE_PERCENTAGE environment variable
  - Sets percentage output for GitHub Actions
  - Handles missing coverage.xml gracefully

This script is designed to be run in GitHub Actions CI environment.
EOF
	exit 0
fi

# Set up environment if not in GitHub Actions
GITHUB_ENV="${GITHUB_ENV:-/dev/null}"
GITHUB_OUTPUT="${GITHUB_OUTPUT:-/dev/null}"

# Helper function to set coverage percentage (uses utils.sh helpers)
output_coverage() {
	local pct="$1"
	set_github_env "COVERAGE_PERCENTAGE" "$pct"
	set_github_output "percentage" "$pct"
	# Also write directly in case set_github_* functions have issues
	echo "COVERAGE_PERCENTAGE=$pct" >>"$GITHUB_ENV"
	echo "percentage=$pct" >>"$GITHUB_OUTPUT"
}

log_info "Extracting coverage percentage from coverage.xml"

# Debug: Show what files exist
log_info "Checking for coverage files in $(pwd)..."
if [[ -f coverage.xml ]]; then
	log_info "coverage.xml exists ($(wc -c <coverage.xml) bytes)"
else
	log_warning "coverage.xml does not exist"
fi
if [[ -f .coverage ]]; then
	log_info ".coverage exists ($(wc -c <.coverage) bytes)"
else
	log_warning ".coverage does not exist"
fi

# Extract coverage percentage from coverage.xml using shared function
if [[ -f coverage.xml ]] && [[ -s coverage.xml ]]; then
	log_info "Attempting to extract coverage from coverage.xml..."

	# Use the shared get_coverage_percentage function from utils.sh
	percentage=$(get_coverage_percentage "coverage.xml")

	if [[ -n "$percentage" ]] && [[ "$percentage" != "0.00" ]]; then
		output_coverage "$percentage"
		log_success "Coverage extracted: $percentage%"
		exit 0
	fi

	# Fallback: try Python script with uv run
	log_info "Attempting Python extraction..."
	if output=$(uv run python scripts/utils/extract-coverage.py 2>&1); then
		if percentage_line=$(echo "$output" | grep "^percentage="); then
			percentage="${percentage_line#percentage=}"
			output_coverage "$percentage"
			log_success "Coverage extracted via Python: $percentage%"
			exit 0
		fi
	fi

	# Final fallback: try python3 directly
	log_info "Attempting python3 fallback..."
	if output=$(python3 scripts/utils/extract-coverage.py 2>&1); then
		if percentage_line=$(echo "$output" | grep "^percentage="); then
			percentage="${percentage_line#percentage=}"
			output_coverage "$percentage"
			log_success "Coverage extracted via python3: $percentage%"
			exit 0
		fi
	fi
fi

# No coverage found - set to 0.0%
output_coverage "0.0"
log_warning "No valid coverage data found, setting coverage to 0.0%"
exit 0
