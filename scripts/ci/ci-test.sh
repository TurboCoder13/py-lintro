#!/bin/bash

# CI Test Script
# Handles running tests in Docker for CI pipeline with GitHub Actions integration

set -e

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [--help]"
    echo ""
    echo "CI Test Script"
    echo "Handles running tests in Docker for CI pipeline with GitHub Actions integration."
    echo ""
    echo "This script:"
    echo "  - Runs integration tests in Docker container"
    echo "  - Captures test output for GitHub Actions"
    echo "  - Generates test summary and reports"
    echo ""
    echo "This script is designed to be run in GitHub Actions CI environment."
    exit 0
fi

# Source shared utilities
source "$(dirname "$0")/../utils/utils.sh"

# Set up step summary if not in GitHub Actions
GITHUB_STEP_SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/null}"
GITHUB_ENV="${GITHUB_ENV:-/dev/null}"

echo "## 🧪 Docker Test Results" >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

echo "### 🧪 Running Integration Tests" >> $GITHUB_STEP_SUMMARY
echo "Running tests in Docker container..." >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

# Run tests in Docker container
set +e  # Don't exit on error
docker run --rm -v "$PWD:/code" py-lintro:latest /app/scripts/local/run-tests.sh > test-output.txt 2>&1
TEST_EXIT_CODE=$?
set -e  # Exit on error again

echo "### 📊 Test Results:" >> $GITHUB_STEP_SUMMARY
echo '```' >> $GITHUB_STEP_SUMMARY
if [ -f test-output.txt ]; then
    cat test-output.txt >> $GITHUB_STEP_SUMMARY
else
    echo "No test output captured" >> $GITHUB_STEP_SUMMARY
fi
echo '```' >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

echo "**Test exit code:** $TEST_EXIT_CODE" >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

# Store the exit code
echo "TEST_EXIT_CODE=$TEST_EXIT_CODE" >> $GITHUB_ENV

echo "### 📋 Summary" >> $GITHUB_STEP_SUMMARY
echo "- **Tests:** All integration tests run in Docker container" >> $GITHUB_STEP_SUMMARY
echo "- **Coverage:** Coverage reports generated" >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

log_success "Docker tests completed with exit code $TEST_EXIT_CODE"

# Exit with the test exit code
exit $TEST_EXIT_CODE 