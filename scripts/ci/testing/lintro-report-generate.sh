#!/usr/bin/env bash
set -e

# Lintro Report Generation Script (Docker)
# Generates comprehensive lintro reports by running lintro inside a Docker container.
# Expects py-lintro:latest to be available locally (pulled from GHCR by the workflow).

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
	echo "Usage: $0 [--help]"
	echo ""
	echo "Lintro Report Generation Script (Docker)"
	echo "Generates comprehensive Lintro reports for GitHub Actions."
	echo ""
	echo "Features:"
	echo "  - Lists available tools in GitHub Actions summary"
	echo "  - Runs Lintro analysis with grid output"
	echo "  - Generates markdown report"
	echo "  - Creates timestamped report directory"
	echo ""
	echo "Requires: py-lintro:latest Docker image (pull from GHCR first)"
	echo "This script is designed to be run in GitHub Actions CI environment."
	exit 0
fi

# Source shared utilities
# SC1091: path is dynamically constructed, file exists at runtime
# shellcheck disable=SC1091
source "$(dirname "$0")/../../utils/utils.sh"

# Common docker run flags matching ci-lintro.sh pattern:
# --user: match host UID/GID for volume writes
# HOME=/tmp: tools like semgrep need a writable home for cache files
DOCKER_RUN="docker run --rm --user $(id -u):$(id -g) -e HOME=/tmp -v $PWD:/code -w /code py-lintro:latest"

{
	echo "## 🔧 Lintro Full Codebase Report"
	echo ""
	echo "**Generated on:** $(date)"
	echo "**Container:** py-lintro:latest"
	echo ""
	echo "### 📋 Available Tools"
	echo '```'
	$DOCKER_RUN lintro list-tools
	echo '```'
	echo ""
	echo "### 🔍 Analysis Results"
	echo '```'
	# Use shared exclude directories
	$DOCKER_RUN lintro check . \
		--exclude "$EXCLUDE_DIRS" \
		--tool-options pydoclint:timeout=120 || true
	echo '```'
} >>"$GITHUB_STEP_SUMMARY"

# Create simple report files
mkdir -p lintro-report
{
	echo "# Lintro Report - $(date)"
	echo ""
	$DOCKER_RUN lintro check . --output-format markdown \
		--exclude "$EXCLUDE_DIRS" \
		--tool-options pydoclint:timeout=120 || true
} >lintro-report/report.md

log_success "Lintro report generated successfully"
log_info "The report is available as a workflow artifact"
log_info "Download it from the Actions tab in the GitHub repository"
