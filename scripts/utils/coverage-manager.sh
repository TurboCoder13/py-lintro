#!/usr/bin/env bash
set -euo pipefail

# coverage-manager.sh - Unified coverage management with subcommands
# Single entry point for all coverage-related operations

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ] || [ $# -eq 0 ]; then
	cat <<'EOF'
Unified coverage management tool with subcommands.

Usage:
  scripts/utils/coverage-manager.sh <COMMAND> [OPTIONS]

Commands:
  extract     Extract coverage percentage from coverage.xml
  badge       Generate and update coverage badge
  comment     Generate PR comment with coverage info
  threshold   Enforce minimum coverage threshold
  status      Get coverage status and color coding

Global Options:
  --help, -h    Show this help message
  --verbose     Enable verbose output
  --dry-run     Show what would be done without executing

Examples:
  scripts/utils/coverage-manager.sh extract --verbose
  scripts/utils/coverage-manager.sh badge --dry-run
  scripts/utils/coverage-manager.sh comment
  scripts/utils/coverage-manager.sh threshold 85
  scripts/utils/coverage-manager.sh status

For command-specific help:
  scripts/utils/coverage-manager.sh <COMMAND> --help
EOF
	exit 0
fi

DRY_RUN=0
VERBOSE=0

# Parse global options first
while [[ $# -gt 0 ]]; do
	case $1 in
	--dry-run)
		DRY_RUN=1
		shift
		;;
	--verbose)
		VERBOSE=1
		shift
		;;
	--help | -h)
		# Show main help and exit
		cat <<'EOF'
Unified coverage management tool with subcommands.

Usage:
  scripts/utils/coverage-manager.sh <COMMAND> [OPTIONS]

Commands:
  extract     Extract coverage percentage from coverage.xml
  badge       Generate and update coverage badge
  comment     Generate PR comment with coverage info
  threshold   Enforce minimum coverage threshold
  status      Get coverage status and color coding

Global Options:
  --help, -h    Show this help message
  --verbose     Enable verbose output
  --dry-run     Show what would be done without executing

Examples:
  scripts/utils/coverage-manager.sh extract --verbose
  scripts/utils/coverage-manager.sh badge --dry-run
  scripts/utils/coverage-manager.sh comment
  scripts/utils/coverage-manager.sh threshold 85
  scripts/utils/coverage-manager.sh status

For command-specific help:
  scripts/utils/coverage-manager.sh <COMMAND> --help
EOF
		exit 0
		;;
	-*)
		# Unknown global option
		echo "Error: Unknown global option: $1" >&2
		exit 1
		;;
	*)
		# This should be the command
		break
		;;
	esac
done

if [ $# -eq 0 ]; then
	echo "Error: Command required" >&2
	echo "Run 'coverage-manager.sh --help' for usage information"
	exit 1
fi

COMMAND="$1"
shift

# Source shared utilities for all coverage operations
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/utils.sh" ]; then
	# SC1091: path is dynamically constructed, file exists at runtime
	# shellcheck source=utils.sh disable=SC1091
	source "${SCRIPT_DIR}/utils.sh"
else
	# Basic logging if utils.sh not available
	log_info() { echo -e "\033[0;34mℹ️  $*\033[0m"; }
	log_verbose() { [ "${VERBOSE:-0}" -eq 1 ] && echo -e "\033[0;36m[verbose] $*\033[0m" || true; }
	log_success() { echo -e "\033[0;32m✅ $*\033[0m"; }
	log_warning() { echo -e "\033[0;33m⚠️  $*\033[0m"; }
	log_error() { echo -e "\033[0;31m❌ $*\033[0m" >&2; }
fi

# Coverage extraction function
extract_coverage() {
	if [ "${1:-}" = "--help" ]; then
		cat <<'EOF'
Extract coverage percentage from coverage.xml.

Usage:
  coverage-manager.sh extract [--help] [--output-env]

Options:
  --help        Show this help message
  --output-env  Set COVERAGE_PERCENTAGE in GitHub Actions environment

Returns:
  Prints coverage percentage to stdout
  Exit code 0 on success, 1 on failure
EOF
		return 0
	fi

	local output_env=0
	while [[ $# -gt 0 ]]; do
		case $1 in
		--output-env)
			output_env=1
			shift
			;;
		*)
			log_error "Unknown option: $1"
			return 1
			;;
		esac
	done

	if [ ! -f "coverage.xml" ]; then
		log_error "coverage.xml not found"
		return 1
	fi

	local coverage_pct
	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would extract coverage from coverage.xml"
		return 0
	fi

	# Extract coverage with detailed error handling
	local extract_output
	extract_output="$(uv run python "${SCRIPT_DIR}/extract-coverage.py" 2>&1)" || {
		log_error "Failed to run extract-coverage.py"
		log_error "Output: $extract_output"
		return 1
	}

	coverage_pct="$(echo "$extract_output" | grep "percentage=" | tail -1 | cut -d'=' -f2 | tr -d '\n' || true)"

	if [ -z "$coverage_pct" ]; then
		log_error "Failed to extract coverage percentage from output"
		log_error "Extract output: $extract_output"
		return 1
	fi

	echo "$coverage_pct"
	log_verbose "Extracted coverage: ${coverage_pct}%" >&2

	if [ $output_env -eq 1 ] && [ -n "${GITHUB_ENV:-}" ]; then
		echo "COVERAGE_PERCENTAGE=$coverage_pct" >>"$GITHUB_ENV"
		log_verbose "Set COVERAGE_PERCENTAGE=$coverage_pct in GitHub environment" >&2
	fi
}

# Coverage status function
get_status() {
	if [ "${1:-}" = "--help" ]; then
		cat <<'EOF'
Get coverage status and color coding.

Usage:
  coverage-manager.sh status [--help] [COVERAGE_PERCENTAGE]

Arguments:
  COVERAGE_PERCENTAGE  Coverage percentage (if not provided, reads from COVERAGE_PERCENTAGE env var or extracts from coverage.xml)

Returns:
  Prints status information in format: STATUS|COLOR|PERCENTAGE
  STATUS: excellent|good|decent|poor|critical
  COLOR: brightgreen|green|yellow|orange|red
EOF
		return 0
	fi

	local coverage_pct="${1:-}"

	# Try to get coverage from: 1) argument, 2) environment variable, 3) coverage.xml
	if [ -z "$coverage_pct" ]; then
		coverage_pct="${COVERAGE_PERCENTAGE:-}"
		log_verbose "Using COVERAGE_PERCENTAGE from environment: ${coverage_pct}%" >&2
	fi

	if [ -z "$coverage_pct" ]; then
		log_verbose "Extracting coverage from coverage.xml" >&2
		if ! coverage_pct="$(extract_coverage)"; then
			return 1
		fi
	fi

	local status color
	if (($(echo "$coverage_pct >= 90" | bc -l 2>/dev/null || echo 0))); then
		status="excellent"
		color="brightgreen"
	elif (($(echo "$coverage_pct >= 80" | bc -l 2>/dev/null || echo 0))); then
		status="good"
		color="green"
	elif (($(echo "$coverage_pct >= 70" | bc -l 2>/dev/null || echo 0))); then
		status="decent"
		color="yellow"
	elif (($(echo "$coverage_pct >= 60" | bc -l 2>/dev/null || echo 0))); then
		status="poor"
		color="orange"
	else
		status="critical"
		color="red"
	fi

	echo "${status}|${color}|${coverage_pct}"
}

# Badge generation function
generate_badge() {
	if [ "${1:-}" = "--help" ]; then
		cat <<'EOF'
Generate and update coverage badge.

Usage:
  coverage-manager.sh badge [--help] [--output PATH]

Options:
  --help           Show this help message
  --output PATH    Output path for badge (default: assets/images/coverage-badge.svg)

Requires:
  - coverage.xml file
  - curl command for badge generation
EOF
		return 0
	fi

	local output_path="assets/images/coverage-badge.svg"
	while [[ $# -gt 0 ]]; do
		case $1 in
		--output)
			output_path="$2"
			shift 2
			;;
		*)
			log_error "Unknown option: $1"
			return 1
			;;
		esac
	done

	local status_info
	if ! status_info="$(get_status)"; then
		return 1
	fi

	local status color coverage_pct
	IFS='|' read -r status color coverage_pct <<<"$status_info"

	log_info "Generating coverage badge: ${coverage_pct}% ($status)"

	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would generate badge: ${coverage_pct}% with color $color"
		log_info "[DRY-RUN] Would save to: $output_path"
		return 0
	fi

	# Create directory if it doesn't exist
	mkdir -p "$(dirname "$output_path")"

	# Try shields.io first (CI uses harden-runner allowlist). Fallback to local.
	local badge_url="https://img.shields.io/badge/coverage-${coverage_pct}%25-${color}.svg"
	if curl -fsSL "$badge_url" -o "$output_path"; then
		log_success "Coverage badge updated from shields.io: $output_path"
		return 0
	fi

	# Fallback: generate badge locally (no network egress)
	local hex_color
	case "$color" in
	brightgreen) hex_color="#4c1" ;;
	green) hex_color="#4c1" ;;
	yellow) hex_color="#dfb317" ;;
	orange) hex_color="#fe7d37" ;;
	red) hex_color="#e05d44" ;;
	*) hex_color="#4c1" ;;
	esac

	cat >"$output_path" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="99" height="20">
    <linearGradient id="b" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linearGradient>
    <clipPath id="a">
        <rect width="99" height="20" rx="3" fill="#fff"/>
    </clipPath>
    <g clip-path="url(#a)">
        <path fill="#555" d="M0 0h63v20H0z"/>
        <path fill="${hex_color}" d="M63 0h36v20H63z"/>
        <path fill="url(#b)" d="M0 0h99v20H0z"/>
    </g>
    <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="110">
        <text x="325" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="530">coverage</text>
        <text x="325" y="140" transform="scale(.1)" textLength="530">coverage</text>
        <text x="800" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="260">${coverage_pct}%</text>
        <text x="800" y="140" transform="scale(.1)" textLength="260">${coverage_pct}%</text>
    </g>
</svg>
EOF

	log_success "Coverage badge updated locally: $output_path"
}

# PR comment generation function
generate_comment() {
	if [ "${1:-}" = "--help" ]; then
		cat <<'EOF'
Generate PR comment with coverage info.

Usage:
  coverage-manager.sh comment [--help] [--output PATH]

Options:
  --help           Show this help message
  --output PATH    Output path for comment file (default: coverage-pr-comment.txt)

Environment Variables:
  JOB_RESULT      Job result status (success/failure)
  GITHUB_RUN_ID   GitHub Actions run ID for links

Note:
  Only generates comment if in PR context (github.event_name == 'pull_request')
EOF
		return 0
	fi

	local output_path="coverage-pr-comment.txt"
	while [[ $# -gt 0 ]]; do
		case $1 in
		--output)
			output_path="$2"
			shift 2
			;;
		*)
			log_error "Unknown option: $1"
			return 1
			;;
		esac
	done

	# Check if we're in a PR context (if utils.sh is available)
	if command -v is_pr_context >/dev/null 2>&1; then
		if ! is_pr_context; then
			log_info "Not in PR context, skipping comment generation"
			return 0
		fi
	fi

	local status_info
	if ! status_info="$(get_status)"; then
		return 1
	fi

	local status color coverage_pct
	IFS='|' read -r status color coverage_pct <<<"$status_info"

	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would generate PR comment with ${coverage_pct}% coverage"
		return 0
	fi

	# Generate comment content
	local job_result="${JOB_RESULT:-success}"
	local run_id="${GITHUB_RUN_ID:-unknown}"
	local github_sha="${GITHUB_SHA:-unknown}"
	local github_repo="${GITHUB_REPOSITORY:-unknown/unknown}"
	local status_emoji build_status status_text

	# Determine coverage status emoji
	if (($(echo "$coverage_pct >= 80" | bc -l 2>/dev/null || echo 0))); then
		status_emoji="✅"
		status_text="Target met (>80%)"
	else
		status_emoji="⚠️"
		status_text="Below target (<80%)"
	fi

	# Determine build status
	if [ "$job_result" != "success" ]; then
		build_status="❌ Tests failed"
	else
		build_status="✅ Tests passed"
	fi

	cat >"$output_path" <<EOF
<!-- coverage-report -->

**Build:** $build_status

**Coverage:** $status_emoji **${coverage_pct}%**

**Status:** $status_text

### 📋 Coverage Details
- **Generated:** $(date +%Y-%m-%d)
- **Commit:** [${github_sha:0:7}](https://github.com/${github_repo}/commit/${github_sha})

### 📁 View Detailed Report
**Direct Link:** [📊 HTML Coverage Report](https://github.com/${github_repo}/actions/runs/${run_id}/artifacts)

Or download manually:
1. Go to the [Actions tab](https://github.com/${github_repo}/actions)
2. Find this workflow run
3. Download the "coverage-report-python-3.13" artifact
4. Extract and open \`index.html\` in your browser
EOF

	log_success "Coverage comment generated: $output_path"
}

# Threshold enforcement function
enforce_threshold() {
	if [ "${1:-}" = "--help" ]; then
		cat <<'EOF'
Enforce minimum coverage threshold.

Usage:
  coverage-manager.sh threshold [--help] <MIN_COVERAGE>

Arguments:
  MIN_COVERAGE    Minimum coverage percentage required

Returns:
  Exit code 0 if coverage meets threshold, 1 if below threshold
EOF
		return 0
	fi

	local min_coverage="${1:-}"
	if [ -z "$min_coverage" ]; then
		log_error "Minimum coverage percentage required"
		return 1
	fi

	local coverage_pct
	if ! coverage_pct="$(extract_coverage)"; then
		return 1
	fi

	log_info "Coverage: ${coverage_pct}% | Threshold: ${min_coverage}%"

	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would check if ${coverage_pct}% >= ${min_coverage}%"
		return 0
	fi

	if (($(echo "$coverage_pct >= $min_coverage" | bc -l 2>/dev/null || echo 0))); then
		log_success "Coverage threshold met: ${coverage_pct}% >= ${min_coverage}%"
		return 0
	else
		log_error "Coverage below threshold: ${coverage_pct}% < ${min_coverage}%"
		return 1
	fi
}

# Main command dispatcher
case "$COMMAND" in
extract)
	extract_coverage "$@"
	;;
status)
	get_status "$@"
	;;
badge)
	generate_badge "$@"
	;;
comment)
	generate_comment "$@"
	;;
threshold)
	enforce_threshold "$@"
	;;
*)
	log_error "Unknown command: $COMMAND"
	echo "Run 'coverage-manager.sh --help' for usage information"
	exit 1
	;;
esac
