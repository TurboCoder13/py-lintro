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

# Output files
REQUIREMENTS_FILE="/tmp/requirements.txt"
UV_OUTPUT_FILE="/tmp/uv-audit-output.txt"
PIP_AUDIT_OUTPUT_FILE="/tmp/pip-audit-output.txt"
COMMENT_FILE="security-audit-comment.txt"

# Track overall status
AUDIT_FAILED=0
UV_VULNS=""
PIP_AUDIT_VULNS=""

log_info "Starting security audit..."

# Step 1: Export dependencies with uv (captures vulnerability output)
log_info "Exporting dependencies with uv..."
UV_EXIT_CODE=0
if ! uv export --no-emit-project >"$REQUIREMENTS_FILE" 2>"$UV_OUTPUT_FILE"; then
	UV_EXIT_CODE=$?
	log_warning "uv export exited with code $UV_EXIT_CODE"
	AUDIT_FAILED=1
else
	log_success "uv export completed successfully"
fi

# Scan both stdout (requirements file) and stderr for vulnerability patterns
# uv may print vulnerability info to either stream
scan_for_vulnerabilities() {
	local file="$1"
	[[ -f "$file" ]] && grep -qi "vulnerability\|GHSA-\|CVE-" "$file" 2>/dev/null
}

# Collect vulnerability output from both files
VULN_OUTPUT=""
if scan_for_vulnerabilities "$UV_OUTPUT_FILE"; then
	VULN_OUTPUT=$(cat "$UV_OUTPUT_FILE")
	AUDIT_FAILED=1
fi
if scan_for_vulnerabilities "$REQUIREMENTS_FILE"; then
	# Append any vulnerability lines from requirements file (shouldn't happen, but be safe)
	REQ_VULNS=$(grep -i "vulnerability\|GHSA-\|CVE-" "$REQUIREMENTS_FILE" 2>/dev/null || true)
	if [[ -n "$REQ_VULNS" ]]; then
		VULN_OUTPUT="${VULN_OUTPUT}${VULN_OUTPUT:+$'\n'}${REQ_VULNS}"
		AUDIT_FAILED=1
	fi
fi
UV_VULNS="$VULN_OUTPUT"

# Step 2: Run pip-audit for additional checks
log_info "Running pip-audit..."
if uv run pip-audit --strict --progress-spinner=off -r "$REQUIREMENTS_FILE" >"$PIP_AUDIT_OUTPUT_FILE" 2>&1; then
	log_success "pip-audit completed - no vulnerabilities found"
else
	PIP_AUDIT_EXIT_CODE=$?
	log_warning "pip-audit exited with code $PIP_AUDIT_EXIT_CODE"
	PIP_AUDIT_VULNS=$(cat "$PIP_AUDIT_OUTPUT_FILE")
	AUDIT_FAILED=1
fi

# Step 3: Generate PR comment
log_info "Generating PR comment..."

if [[ "$AUDIT_FAILED" -eq 0 ]]; then
	STATUS="✅ PASSED"
	CONTENT="<!-- security-audit-report -->

No security vulnerabilities found in dependencies.

### 🔍 Checks Performed:
- **uv audit**: Checked for known vulnerabilities in lockfile
- **pip-audit**: Scanned dependencies against PyPI advisory database"
else
	STATUS="⚠️ VULNERABILITIES FOUND"
	CONTENT="<!-- security-audit-report -->

Security vulnerabilities were detected in project dependencies.

### 🔍 Checks Performed:
- **uv audit**: Checked for known vulnerabilities in lockfile
- **pip-audit**: Scanned dependencies against PyPI advisory database"

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
fi

# Generate the comment file using shared function
generate_pr_comment "🔐 Security Audit" "$STATUS" "$CONTENT" "$COMMENT_FILE" "uv + pip-audit"

# Set output for GitHub Actions
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
	echo "audit_failed=$AUDIT_FAILED" >>"$GITHUB_OUTPUT"
fi

# Exit with appropriate code
if [[ "$AUDIT_FAILED" -eq 1 ]]; then
	log_error "Security audit found vulnerabilities"
	exit 1
else
	log_success "Security audit passed"
	exit 0
fi
