#!/bin/bash

# Lintro Report Generation Script
# Generates comprehensive lintro reports for the codebase

# Source shared utilities
source "$(dirname "$0")/utils.sh"

echo "## 🔧 Lintro Full Codebase Report" >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY
echo "**Generated on:** $(date)" >> $GITHUB_STEP_SUMMARY
echo "**Note:** Includes all available tools." >> $GITHUB_STEP_SUMMARY
echo "Missing tools are skipped gracefully." >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

echo "### 📋 Available Tools" >> $GITHUB_STEP_SUMMARY
echo '```' >> $GITHUB_STEP_SUMMARY
./scripts/local-lintro.sh list-tools >> $GITHUB_STEP_SUMMARY
echo '```' >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

echo "### 🔍 Analysis Results" >> $GITHUB_STEP_SUMMARY
echo '```' >> $GITHUB_STEP_SUMMARY
# Use shared exclude directories
./scripts/local-lintro.sh check . --format grid \
    --exclude "$EXCLUDE_DIRS" >> $GITHUB_STEP_SUMMARY || true
echo '```' >> $GITHUB_STEP_SUMMARY

# Create simple report files
mkdir -p lintro-report
echo "# Lintro Report - $(date)" > lintro-report/report.md
echo "" >> lintro-report/report.md
echo "**Note:** Includes available tools." >> lintro-report/report.md
echo "Missing tools skipped gracefully." >> lintro-report/report.md
echo "" >> lintro-report/report.md
FORMAT="markdown"
./scripts/local-lintro.sh check . --format $FORMAT \
    --exclude "$EXCLUDE_DIRS" >> lintro-report/report.md || true

log_success "Lintro report generated successfully"
log_info "The report is available as a workflow artifact"
log_info "Download it from the Actions tab in the GitHub repository"
log_info ""
log_info "💡 For full tool coverage, run with all system tools installed"
log_info "🔧 Use './scripts/install.sh && ./scripts/local-lintro.sh'"
log_info "   locally for complete analysis" 