#!/bin/bash

# Coverage PR Comment Script
# Generates and posts comments to PRs with coverage information

# Source shared utilities
source "$(dirname "$0")/../utils/utils.sh"

# Check if we're in a PR context
if ! is_pr_context; then
    log_info "Not in a PR context, skipping coverage comment generation"
    exit 0
fi

# Get coverage value using shared function
COVERAGE_VALUE=$(get_coverage_value)
COVERAGE_STATUS=$(get_coverage_status "$COVERAGE_VALUE")

# Determine status text
if [ "$COVERAGE_STATUS" = "✅" ]; then
    STATUS_TEXT="Target met (>80%)"
else
    STATUS_TEXT="Below target (<80%)"
fi

# Create the comment content with marker
CONTENT="<!-- coverage-report -->

**Coverage:** $COVERAGE_STATUS **$COVERAGE_VALUE%**

**Status:** $STATUS_TEXT

### 📋 Coverage Details
- **Generated:** $(date +%Y-%m-%d)
- **Commit:** [$GITHUB_SHA](https://github.com/$GITHUB_REPOSITORY/commit/$GITHUB_SHA)

### 📁 View Detailed Report
**Direct Link:** [📊 HTML Coverage Report](https://github.com/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID/artifacts)

Or download manually:
1. Go to the [Actions tab](https://github.com/$GITHUB_REPOSITORY/actions)
2. Find this workflow run
3. Download the \"coverage-report-python-3.13\" artifact
4. Extract and open \`index.html\` in your browser"

# Generate PR comment using shared function
generate_pr_comment "📊 Code Coverage Report" "$STATUS_TEXT" "$CONTENT" "coverage-pr-comment.txt" 