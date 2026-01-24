#!/usr/bin/env bash
set -e

# Lintro Report Generation Script
# Generates comprehensive lintro reports for the codebase

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
	echo "Usage: $0 [--help]"
	echo ""
	echo "Lintro Report Generation Script"
	echo "Generates comprehensive Lintro reports for GitHub Actions."
	echo ""
	echo "Features:"
	echo "  - Lists available tools in GitHub Actions summary"
	echo "  - Runs Lintro analysis with grid output"
	echo "  - Generates markdown report"
	echo "  - Creates timestamped report directory"
	echo ""
	echo "This script is designed to be run in GitHub Actions CI environment."
	exit 0
fi

# Source shared utilities
# SC1091: path is dynamically constructed, file exists at runtime
# shellcheck disable=SC1091
source "$(dirname "$0")/../../utils/utils.sh"

{
	echo "## 🔧 Lintro Full Codebase Report"
	echo ""
	echo "**Generated on:** $(date)"
	echo "**Note:** Includes all available tools."
	echo "Missing tools are skipped gracefully."
	echo ""
	echo "### 📋 Available Tools"
	echo '```'
	./scripts/local/local-lintro.sh list-tools
	echo '```'
	echo ""
	echo "### 🔍 Analysis Results"
	echo '```'
	# Use shared exclude directories
	./scripts/local/local-lintro.sh check . \
		--exclude "$EXCLUDE_DIRS" || true
	echo '```'
} >>"$GITHUB_STEP_SUMMARY"

# Create simple report files
mkdir -p lintro-report
{
	echo "# Lintro Report - $(date)"
	echo ""
	echo "**Note:** Includes available tools."
	echo "Missing tools skipped gracefully."
	echo ""
	FORMAT="markdown"
	./scripts/local/local-lintro.sh check . --output-format "$FORMAT" \
		--exclude "$EXCLUDE_DIRS" || true
} >lintro-report/report.md

log_success "Lintro report generated successfully"
log_info "The report is available as a workflow artifact"
log_info "Download it from the Actions tab in the GitHub repository"
log_info ""
log_info "💡 For full tool coverage, run with all system tools installed"
log_info "🔧 Use './scripts/utils/install.sh && ./scripts/local/local-lintro.sh'"
log_info "   locally for complete analysis"
