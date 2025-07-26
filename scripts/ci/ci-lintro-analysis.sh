#!/bin/bash

# CI Lintro Analysis Script
# Handles the lintro formatting and checking steps for CI pipeline

set -e

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [--help]"
    echo ""
    echo "CI Lintro Analysis Script"
    echo "Runs Lintro formatting and checking steps for CI pipeline with GitHub Actions integration."
    echo ""
    echo "Features:"
    echo "  - Applies formatting fixes with 'lintro format'"
    echo "  - Performs code quality checks with 'lintro check'"
    echo "  - Generates GitHub Actions step summaries"
    echo "  - Extracts summary for PR comments"
    echo ""
    echo "This script is designed to be run in GitHub Actions CI environment."
    exit 0
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "## 🔧 Lintro Code Quality & Analysis" >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

# Step 1: Run Lintro Formatting
echo "### 🛠️ Step 1: Applying Formatting Fixes" >> $GITHUB_STEP_SUMMARY
echo "Running \`lintro format\` to apply any relevant fixes..." >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

# Run lintro format to apply formatting fixes
set +e  # Don't exit on error
uv run lintro format . > fmt-output.txt 2>&1
FMT_EXIT_CODE=$?
set -e  # Exit on error again

echo "### 📋 Formatting Results:" >> $GITHUB_STEP_SUMMARY
echo '```' >> $GITHUB_STEP_SUMMARY
if [ -f fmt-output.txt ]; then
    cat fmt-output.txt >> $GITHUB_STEP_SUMMARY
else
    echo "No formatting output captured" >> $GITHUB_STEP_SUMMARY
fi
echo '```' >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

echo "**Formatting exit code:** $FMT_EXIT_CODE" >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

# Step 2: Run Lintro Checks
echo "### 🔍 Step 2: Running Linting Checks" >> $GITHUB_STEP_SUMMARY
echo "Running \`lintro check\` to perform code quality analysis..." >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

# Run lintro check to perform linting checks
set +e  # Don't exit on error
uv run lintro check . > chk-output.txt 2>&1
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

# Extract only the summary table and ASCII art for PR comment
if [ -f chk-output.txt ]; then
    # Look for the summary section
    sed -n '/^📋 EXECUTION SUMMARY$/,$p' chk-output.txt > chk-summary.txt
    # If no summary found, try alternative patterns
    if [ ! -s chk-summary.txt ]; then
        sed -n '/^📊 SUMMARY$/,$p' chk-output.txt > chk-summary.txt
    fi
    if [ ! -s chk-summary.txt ]; then
        sed -n '/^SUMMARY$/,$p' chk-output.txt > chk-summary.txt
    fi
    # If still no summary, use the last 20 lines as fallback
    if [ ! -s chk-summary.txt ]; then
        tail -20 chk-output.txt > chk-summary.txt
    fi
else
    echo "No linting output captured" > chk-summary.txt
fi

# Store the exit code for the PR comment step
echo "CHK_EXIT_CODE=$CHK_EXIT_CODE" >> $GITHUB_ENV

echo "### 📋 Summary" >> $GITHUB_STEP_SUMMARY
echo "- **Step 1:** Formatting fixes applied with \`lintro format\`" >> $GITHUB_STEP_SUMMARY
echo "- **Step 2:** Code quality checks performed with \`lintro check\`" >> $GITHUB_STEP_SUMMARY
echo "- **Test files:** Excluded via \`.lintro-ignore\`" >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

echo "---" >> $GITHUB_STEP_SUMMARY
echo "🚀 **Lintro** provides a unified interface for multiple code quality tools!" >> $GITHUB_STEP_SUMMARY
echo "This ensures consistent formatting and linting across different file types." >> $GITHUB_STEP_SUMMARY

# Exit with the check exit code
exit $CHK_EXIT_CODE 