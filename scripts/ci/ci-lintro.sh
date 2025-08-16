#!/bin/bash

# CI Lintro Analysis Script  
# Handles running lintro analysis in Docker for CI pipeline with GitHub Actions integration

set -e

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [--help]"
    echo ""
    echo "CI Lintro Analysis Script"
    echo "Runs Lintro analysis in Docker for CI pipeline with GitHub Actions integration."
    echo ""
    echo "Features:"
    echo "  - Runs Lintro in Docker container"
    echo "  - Excludes test files via .lintro-ignore"
    echo "  - Generates GitHub Actions summaries"
    echo "  - Stores exit code for PR comment step"
    echo ""
    echo "This script is designed to be run in GitHub Actions CI environment."
    exit 0
fi

# Source shared utilities
source "$(dirname "$0")/../utils/utils.sh"

# Set up step summary if not in GitHub Actions
GITHUB_STEP_SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/null}"
GITHUB_ENV="${GITHUB_ENV:-/dev/null}"

echo "## 🔧 Lintro Code Quality & Analysis" >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

echo "### 🛠️ Step 1: Running Lintro Checks" >> $GITHUB_STEP_SUMMARY
echo "Running \`lintro check\` in Docker container against the entire project..." >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

# Run lintro check in Docker container against the entire project
# The .lintro-ignore file will automatically exclude test_samples/
set +e  # Don't exit on error
# Use the image entrypoint to invoke lintro directly; avoid shell passthrough
docker run --rm -v "$PWD:/code" -w /code py-lintro:latest lintro check . > chk-output.txt 2>&1
CHK_EXIT_CODE=$?
set -e  # Exit on error again

echo "### 📊 Linting Results:" >> $GITHUB_STEP_SUMMARY
echo '```' >> $GITHUB_STEP_SUMMARY
if [ -f chk-output.txt ]; then
    cat chk-output.txt >> $GITHUB_STEP_SUMMARY
else
    echo "No linting output captured" >> $GITHUB_STEP_SUMMARY
fi
echo '```' >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

echo "**Linting exit code:** $CHK_EXIT_CODE" >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

# Keep full chk-output.txt; summarization now handled in PR comment script
if [ ! -f chk-output.txt ]; then
    echo "No linting output captured" > chk-output.txt
fi

# Store the exit code for the PR comment step
echo "CHK_EXIT_CODE=$CHK_EXIT_CODE" >> $GITHUB_ENV

echo "### 📋 Summary" >> $GITHUB_STEP_SUMMARY
echo "- **Step 1:** Code quality checks performed with \`lintro check\` in Docker" >> $GITHUB_STEP_SUMMARY
echo "- **Test files:** Excluded via \`.lintro-ignore\`" >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

echo "---" >> $GITHUB_STEP_SUMMARY
echo "🚀 **Lintro** provides a unified interface for multiple code quality tools!" >> $GITHUB_STEP_SUMMARY
echo "This ensures consistent formatting and linting across different file types." >> $GITHUB_STEP_SUMMARY

log_success "Docker lintro analysis completed with exit code $CHK_EXIT_CODE"

# Exit with the check exit code
exit $CHK_EXIT_CODE 