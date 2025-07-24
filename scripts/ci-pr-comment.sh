#!/bin/bash

# CI PR Comment Script
# Generates and posts comments to PRs with lintro analysis results

# Source shared utilities
source "$(dirname "$0")/utils.sh"

# Check if we're in a PR context
if ! is_pr_context; then
    log_info "Not in a PR context, skipping comment generation"
    exit 0
fi

# Read the summary file
if [ -f chk-summary.txt ]; then
    OUTPUT=$(cat chk-summary.txt)
    
    # Check if there are any issues found
    if echo "$OUTPUT" | grep -q "❌\|FAILED\|ERROR"; then
        STATUS="⚠️ ISSUES FOUND"
    else
        STATUS="✅ PASSED"
    fi
else
    OUTPUT="❌ Analysis failed - check the CI logs for details"
    STATUS="❌ FAILED"
fi

# Create the comment content with marker
CONTENT="<!-- lintro-report -->

**Workflow:**
1. ✅ Applied formatting fixes with \`lintro fmt\`
2. 🔍 Performed code quality checks with \`lintro chk\`

### 📋 Results:
\`\`\`
$OUTPUT
\`\`\`"

# Generate PR comment using shared function
generate_pr_comment "🔧 Lintro Code Quality Analysis" "$STATUS" "$CONTENT" "pr-comment.txt" 