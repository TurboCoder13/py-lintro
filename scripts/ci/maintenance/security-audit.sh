#!/usr/bin/env bash
#
# Security Audit Script
# Comprehensive security verification for workflows, actions, and scripts
#
# Usage: scripts/ci/security-audit.sh [--help] [--fix]

set -euo pipefail

# Configuration
WORKFLOWS_DIR=".github/workflows"
ACTIONS_DIR=".github/actions"
SCRIPTS_DIR="scripts"
EXIT_CODE=0

show_help() {
	cat <<EOF
Security Audit Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --fix       Attempt to automatically fix issues
    --help      Show this help message

DESCRIPTION:
    Performs comprehensive security auditing of:
    - GitHub Actions SHA pinning
    - Hardened runner usage consistency  
    - Shell script error handling
    - Endpoint allowlisting patterns
    - Script permissions and shebangs

EXIT CODES:
    0    All security checks passed
    1    Security issues found
    2    Script error
EOF
}

# Check for help flag before sourcing utils (to avoid path issues)
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
	show_help
	exit 0
fi

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
# SC1091: path is dynamically constructed, file exists at runtime
# shellcheck source=../../utils/utils.sh disable=SC1091
source "${SCRIPT_DIR}/../../utils/utils.sh"

check_sha_pinning() {
	log_info "Checking SHA pinning for GitHub Actions..."

	local violations=0

	# Check for version tags instead of SHA pins
	if grep -r "uses:.*@v[0-9]" "$WORKFLOWS_DIR" "$ACTIONS_DIR" 2>/dev/null; then
		log_error "Found version tag usage instead of SHA pinning"
		violations=$((violations + 1))
	fi

	# Check for missing SHA pins (actions without @), excluding local actions
	if grep -r "uses:" "$WORKFLOWS_DIR" "$ACTIONS_DIR" | grep -v "@[a-fA-F0-9]\{40\}" | grep -v "@[a-fA-F0-9]\{7,\}.*#" | grep -v "uses: \."; then
		log_error "Found actions without proper SHA pinning"
		violations=$((violations + 1))
	fi

	if [ $violations -eq 0 ]; then
		log_success "SHA pinning check passed"
	else
		log_error "Found $violations SHA pinning violations"
		return 1
	fi
}

check_hardened_runners() {
	log_info "Checking hardened runner consistency..."

	local violations=0

	# Check for workflows without hardened runners
	while IFS= read -r -d '' workflow; do
		if [ -f "$workflow" ] && ! grep -q "harden-runner\|docker-setup\|harden-and-checkout" "$workflow"; then
			log_warning "Workflow $(basename "$workflow") may be missing hardened runner"
			violations=$((violations + 1))
		fi
	done < <(find "$WORKFLOWS_DIR" -name "*.yml" -print0)

	# Enforce direct StepSecurity harden-runner usage (no composites)
	if grep -R "uses: .*\.github/actions/harden-and-checkout@" "$WORKFLOWS_DIR" "$ACTIONS_DIR" 2>/dev/null; then
		log_warning "Found composite 'harden-and-checkout' usage; prefer direct step-security/harden-runner"
		violations=$((violations + 1))
	fi
	if grep -R "uses: .*\.github/actions/docker-setup@" "$WORKFLOWS_DIR" "$ACTIONS_DIR" 2>/dev/null; then
		log_warning "Found composite 'docker-setup' usage; prefer explicit steps with direct harden-runner"
		violations=$((violations + 1))
	fi

	if [ $violations -eq 0 ]; then
		log_success "Hardened runner check passed"
	else
		log_warning "Found $violations workflows that may need hardened runners"
	fi
}

check_endpoint_consistency() {
	log_info "Checking endpoint allowlisting patterns..."

	local violations=0

	# Require explicit endpoints in workflows (no env/vars indirection)
	# Flag any allowed-endpoints that reference env/vars instead of literal host:port entries
	if grep -R "allowed-endpoints:\s*[|>]" "$WORKFLOWS_DIR" "$ACTIONS_DIR" 2>/dev/null | grep -E "\$\{\{\s*(env|vars)\.[A-Z0-9_]+\s*\}\}" >/dev/null; then
		log_warning "Found allowed-endpoints using env/vars; replace with explicit host:port entries"
		violations=$((violations + 1))
	fi

	if [ $violations -eq 0 ]; then
		log_success "Endpoint allowlisting check passed"
	else
		log_warning "Found $violations endpoint consistency issues"
	fi
}

check_script_security() {
	log_info "Checking shell script security..."

	local violations=0
	local checked=0

	# Check all shell scripts for security practices
	while IFS= read -r -d '' script; do
		if [[ -f "$script" && ("$script" == *.sh) ]]; then
			checked=$((checked + 1))

			# Check for proper error handling
			if ! grep -q "set -[euo]" "$script"; then
				log_error "Script $script missing proper error handling (set -euo pipefail)"
				violations=$((violations + 1))
			fi

			# Check for proper shebang
			if ! head -n1 "$script" | grep -q "#!/"; then
				log_error "Script $script missing shebang"
				violations=$((violations + 1))
			fi

			# Check for executable permissions
			if [ ! -x "$script" ]; then
				log_error "Script $script not executable"
				violations=$((violations + 1))
			fi
		fi
	done < <(find "$SCRIPTS_DIR" -name "*.sh" -print0)

	log_info "Checked $checked shell scripts"

	if [ $violations -eq 0 ]; then
		log_success "Shell script security check passed"
	else
		log_error "Found $violations shell script security issues"
		return 1
	fi
}

check_inline_shell() {
	log_info "Checking for inline shell in workflows..."

	local violations=0

	# Look for complex inline shell that should be in scripts
	if grep -r "run:.*|" "$WORKFLOWS_DIR" | grep -v "echo\|cat\|head\|tail"; then
		log_warning "Found complex inline shell that could be moved to scripts"
		violations=$((violations + 1))
	fi

	# Look for multi-line run blocks
	if grep -r -A5 "run: |" "$WORKFLOWS_DIR" | grep -c "^-" >/dev/null; then
		log_warning "Found multi-line run blocks that could be moved to scripts"
		violations=$((violations + 1))
	fi

	if [ $violations -eq 0 ]; then
		log_success "Inline shell check passed"
	else
		log_warning "Found $violations potential inline shell improvements"
	fi
}

check_secrets_exposure() {
	log_info "Checking for potential secrets exposure..."

	local violations=0

	# Check for secrets in echo commands (excluding environment variable setting)
	if grep -r "echo.*secret\|echo.*token\|echo.*key" "$WORKFLOWS_DIR" "$ACTIONS_DIR" "$SCRIPTS_DIR" 2>/dev/null | grep -v "GITHUB_ENV\|>>.*ENV"; then
		log_error "Found potential secrets exposure in echo commands"
		violations=$((violations + 1))
	fi

	# Check for secrets in log commands (excluding this script's own logging)
	if grep -r "log.*secret\|log.*token\|log.*key" "$SCRIPTS_DIR" 2>/dev/null | grep -v "security-audit.sh"; then
		log_error "Found potential secrets exposure in log commands"
		violations=$((violations + 1))
	fi

	if [ $violations -eq 0 ]; then
		log_success "Secrets exposure check passed"
	else
		log_error "Found $violations potential secrets exposure issues"
		return 1
	fi
}

main() {
	local fix_mode=false

	# Parse arguments
	while [[ $# -gt 0 ]]; do
		case $1 in
		--fix)
			fix_mode=true
			shift
			;;
		--help | -h)
			show_help
			exit 0
			;;
		*)
			log_error "Unknown option: $1"
			show_help
			exit 2
			;;
		esac
	done

	log_info "Starting comprehensive security audit..."

	# Run all security checks
	check_sha_pinning || EXIT_CODE=1
	check_hardened_runners || EXIT_CODE=1
	check_endpoint_consistency || EXIT_CODE=1
	check_script_security || EXIT_CODE=1
	check_inline_shell || EXIT_CODE=1
	check_secrets_exposure || EXIT_CODE=1

	echo ""
	if [ $EXIT_CODE -eq 0 ]; then
		log_success "🔒 All security checks passed!"
		log_info "Your workflows, actions, and scripts follow security best practices."
	else
		log_error "🚨 Security issues found!"
		log_info "Review the issues above and fix before proceeding."

		if [ "$fix_mode" = true ]; then
			log_info "Fix mode requested but not implemented for safety."
			log_info "Please review and fix issues manually."
		fi
	fi

	exit $EXIT_CODE
}

main "$@"
