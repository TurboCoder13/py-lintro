#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# For license details, see the repository root LICENSE file.
#
# security-audit.sh - Run security audit on dependencies and generate PR comment
#
# This script:
#   1. Exports dependencies using uv (which checks for vulnerabilities)
#   2. Runs pip-audit for additional security checks
#   3. Generates a PR comment file with the results
#
# Usage:
#   ./scripts/ci/security-audit.sh
#
# Environment:
#   GITHUB_OUTPUT - GitHub Actions output file (optional)

set -euo pipefail

# Show help if requested
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Usage: security-audit.sh

Run security audit on Python dependencies and generate PR comment.

This script exports dependencies using uv (which checks for vulnerabilities),
runs pip-audit for additional checks, and generates a PR comment with results.

Exit codes:
  0 - No vulnerabilities found
  1 - Vulnerabilities found or audit failed
EOF
	exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source shared utilities
# shellcheck source=../utils/utils.sh disable=SC1091
source "$SCRIPT_DIR/../utils/utils.sh"

# Output files - use mktemp for security and to avoid collisions
REQUIREMENTS_FILE=$(mktemp --tmpdir requirements.XXXXXX.txt)
UV_OUTPUT_FILE=$(mktemp --tmpdir uv-audit-output.XXXXXX.txt)
PIP_AUDIT_OUTPUT_FILE=$(mktemp --tmpdir pip-audit-output.XXXXXX.txt)
COMMENT_FILE="security-audit-comment.txt"

# Cleanup temp files on exit
# shellcheck disable=SC2329 # Function is invoked via trap, not directly
cleanup_temp_files() {
	rm -f "$REQUIREMENTS_FILE" "$UV_OUTPUT_FILE" "$PIP_AUDIT_OUTPUT_FILE"
}
trap cleanup_temp_files EXIT

# Track status separately: execution errors vs vulnerability findings
AUDIT_FAILED=0
UV_VULNS=""
PIP_AUDIT_VULNS=""
UV_ERROR=""
PIP_AUDIT_ERROR=""

log_info "Starting security audit..."

# Scan file for vulnerability patterns
# Avoids false positives on phrases like "no vulnerabilities found"
scan_for_vulnerabilities() {
	local file="$1"
	[[ -f "$file" ]] || return 1

	# First check for explicit vulnerability IDs (GHSA-*, CVE-*)
	if grep -qEi 'GHSA-|CVE-[0-9]{4}-[0-9]+' "$file" 2>/dev/null; then
		return 0
	fi

	# Then check for "vulnerability" but exclude negated phrases
	if grep -Ei '\bvulnerabilit' "$file" 2>/dev/null |
		grep -qviE 'no .*vulnerabilit|none .*vulnerabilit|without .*vulnerabilit|0 .*vulnerabilit'; then
		return 0
	fi

	return 1
}

# Step 1: Export dependencies with uv (captures vulnerability output)
log_info "Exporting dependencies with uv..."
UV_EXIT_CODE=0
uv export --no-emit-project >"$REQUIREMENTS_FILE" 2>"$UV_OUTPUT_FILE" || UV_EXIT_CODE=$?

if [[ "$UV_EXIT_CODE" -ne 0 ]]; then
	# Check if failure is due to vulnerabilities or an actual error
	if scan_for_vulnerabilities "$UV_OUTPUT_FILE"; then
		log_warning "uv export found vulnerabilities"
		UV_VULNS=$(cat "$UV_OUTPUT_FILE")
	else
		log_error "uv export failed with code $UV_EXIT_CODE"
		UV_ERROR=$(cat "$UV_OUTPUT_FILE")
		AUDIT_FAILED=1
	fi
else
	log_success "uv export completed successfully"
	# Still check for vulnerability patterns even on success (uv may warn without failing)
	if scan_for_vulnerabilities "$UV_OUTPUT_FILE"; then
		UV_VULNS=$(cat "$UV_OUTPUT_FILE")
	fi
fi

# Also check requirements file for any vulnerability info (shouldn't happen, but be safe)
if scan_for_vulnerabilities "$REQUIREMENTS_FILE"; then
	REQ_VULNS=$(grep -i "vulnerability\|GHSA-\|CVE-" "$REQUIREMENTS_FILE" 2>/dev/null || true)
	if [[ -n "$REQ_VULNS" ]]; then
		UV_VULNS="${UV_VULNS}${UV_VULNS:+$'\n'}${REQ_VULNS}"
	fi
fi

# Step 2: Run pip-audit for additional checks
log_info "Running pip-audit..."
PIP_AUDIT_EXIT_CODE=0
uv run pip-audit --strict --progress-spinner=off -r "$REQUIREMENTS_FILE" >"$PIP_AUDIT_OUTPUT_FILE" 2>&1 || PIP_AUDIT_EXIT_CODE=$?

if [[ "$PIP_AUDIT_EXIT_CODE" -eq 0 ]]; then
	log_success "pip-audit completed - no vulnerabilities found"
else
	# Check if failure is due to vulnerabilities or an actual error
	if scan_for_vulnerabilities "$PIP_AUDIT_OUTPUT_FILE"; then
		log_warning "pip-audit found vulnerabilities"
		PIP_AUDIT_VULNS=$(cat "$PIP_AUDIT_OUTPUT_FILE")
	else
		log_error "pip-audit failed with code $PIP_AUDIT_EXIT_CODE"
		PIP_AUDIT_ERROR=$(cat "$PIP_AUDIT_OUTPUT_FILE")
		AUDIT_FAILED=1
	fi
fi

# Determine if we have actual vulnerability findings
HAS_VULNS=0
if [[ -n "$UV_VULNS" ]] || [[ -n "$PIP_AUDIT_VULNS" ]]; then
	HAS_VULNS=1
fi

# Step 3: Generate PR comment
log_info "Generating PR comment..."

CHECKS_PERFORMED="### 🔍 Checks Performed:
- **uv audit**: Checked for known vulnerabilities in lockfile
- **pip-audit**: Scanned dependencies against PyPI advisory database"

if [[ "$AUDIT_FAILED" -eq 1 ]]; then
	# Audit execution failed
	STATUS="❌ AUDIT FAILED"
	CONTENT="<!-- security-audit-report -->

The security audit encountered errors during execution.

$CHECKS_PERFORMED"

	if [[ -n "$UV_ERROR" ]]; then
		CONTENT="$CONTENT

### ❌ uv export Error:
\`\`\`
$UV_ERROR
\`\`\`"
	fi

	if [[ -n "$PIP_AUDIT_ERROR" ]]; then
		CONTENT="$CONTENT

### ❌ pip-audit Error:
\`\`\`
$PIP_AUDIT_ERROR
\`\`\`"
	fi

	CONTENT="$CONTENT

### 🔧 Recommended Actions:
1. Check the error messages above
2. Verify dependencies can be resolved
3. Re-run the audit after fixing any issues"

elif [[ "$HAS_VULNS" -eq 1 ]]; then
	# Vulnerabilities found
	STATUS="⚠️ VULNERABILITIES FOUND"
	CONTENT="<!-- security-audit-report -->

Security vulnerabilities were detected in project dependencies.

$CHECKS_PERFORMED"

	if [[ -n "$UV_VULNS" ]]; then
		CONTENT="$CONTENT

### 🚨 uv Vulnerability Report:
\`\`\`
$UV_VULNS
\`\`\`"
	fi

	if [[ -n "$PIP_AUDIT_VULNS" ]]; then
		CONTENT="$CONTENT

### 🚨 pip-audit Report:
\`\`\`
$PIP_AUDIT_VULNS
\`\`\`"
	fi

	CONTENT="$CONTENT

### 🔧 Recommended Actions:
1. Review the vulnerabilities above
2. Update affected packages if fixes are available
3. If no fix is available, assess the risk and document exceptions"

else
	# All clear
	STATUS="✅ PASSED"
	CONTENT="<!-- security-audit-report -->

No security vulnerabilities found in dependencies.

$CHECKS_PERFORMED"
fi

# Generate the comment file using shared function
generate_pr_comment "🔐 Security Audit" "$STATUS" "$CONTENT" "$COMMENT_FILE" "uv + pip-audit"

# Set output for GitHub Actions
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
	echo "audit_failed=$AUDIT_FAILED" >>"$GITHUB_OUTPUT"
	echo "has_vulns=$HAS_VULNS" >>"$GITHUB_OUTPUT"
fi

# Exit with appropriate code
if [[ "$AUDIT_FAILED" -eq 1 ]]; then
	log_error "Security audit failed to execute"
	exit 1
elif [[ "$HAS_VULNS" -eq 1 ]]; then
	log_error "Security audit found vulnerabilities"
	exit 1
else
	log_success "Security audit passed"
	exit 0
fi
