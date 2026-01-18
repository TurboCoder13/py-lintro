#!/usr/bin/env bash
set -euo pipefail

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
	echo "Usage: $0 [--help|-h]"
	echo ""
	echo "CI PR Comment Script"
	echo "Generates a PR comment from chk-summary.txt within a GitHub Actions run."
	echo ""
	echo "This script is intended for CI and will no-op outside pull_request events."
	exit 0
fi

# CI PR Comment Script
# Generates and posts comments to PRs with lintro analysis results

# Source shared utilities
source "$(dirname "$0")/../utils/utils.sh"

# Check if we're in a PR context
if ! is_pr_context; then
	log_info "Not in a PR context, skipping comment generation"
	exit 0
fi

# Read the summary file (robust extraction) and derive status from exit code
if [ -f chk-output.txt ]; then
	# Try to extract from the EXECUTION SUMMARY section regardless of emoji
	start_line=$(grep -n "EXECUTION SUMMARY" chk-output.txt | head -n1 | cut -d: -f1 || true)
	if [ -n "${start_line:-}" ]; then
		tail -n +"$start_line" chk-output.txt >chk-summary.txt || true
	else
		# Fallback to last 50 lines to capture table if header not found
		tail -n 50 chk-output.txt >chk-summary.txt || true
	fi
fi

if [ -f chk-summary.txt ]; then
	OUTPUT=$(cat chk-summary.txt)
else
	OUTPUT="❌ Analysis failed - check the CI logs for details"
fi

# Prefer the recorded exit code to determine status; fallback to grep
if [ "${CHK_EXIT_CODE:-1}" != "0" ]; then
	STATUS="⚠️ ISSUES FOUND"
else
	if echo "$OUTPUT" | grep -q "❌\|FAILED\|ERROR"; then
		STATUS="⚠️ ISSUES FOUND"
	else
		STATUS="✅ PASSED"
	fi
fi

# Create the comment content with marker
CONTENT="<!-- lintro-report -->

**Workflow:**
1. ✅ Applied formatting fixes with \`lintro format\`
2. 🔍 Performed code quality checks with \`lintro check\`

### 📋 Results:
\`\`\`
$OUTPUT
\`\`\`"

# Generate PR comment using shared function
generate_pr_comment "🔧 Lintro Code Quality Analysis" "$STATUS" "$CONTENT" "pr-comment.txt"
