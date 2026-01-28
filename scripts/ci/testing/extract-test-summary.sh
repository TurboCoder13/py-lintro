#!/usr/bin/env bash
set -euo pipefail

# extract-test-summary.sh - Extract test summary from pytest output
#
# Parses the test output to extract passed/failed/skipped/total/duration
# and saves to a JSON file for use in PR comments.

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
	cat <<'EOF'
Usage: extract-test-summary.sh [OPTIONS] <test-output-file> [output-json-file]

Extract test summary from pytest output and save to JSON.

Arguments:
  test-output-file   Path to file containing pytest output
  output-json-file   Path to write the JSON summary (default: test-summary.json)

Options:
  -q, --quiet        Suppress summary output (only write JSON)
  -h, --help         Show this help message

Example:
  ./extract-test-summary.sh test-output.log test-summary.json
  ./extract-test-summary.sh --quiet test-output.log

Environment Variables:
  If no input file is provided or file doesn't exist, the script will use:
  TEST_PASSED, TEST_FAILED, TEST_SKIPPED, TEST_ERRORS, TEST_TOTAL, TEST_DURATION
EOF
	exit 0
fi

# Parse options
QUIET=0
while [[ "${1:-}" == -* ]]; do
	case "$1" in
	-q | --quiet)
		QUIET=1
		shift
		;;
	*)
		echo "Unknown option: $1" >&2
		exit 1
		;;
	esac
done

# Source shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../utils/utils.sh disable=SC1091
source "$SCRIPT_DIR/../../utils/utils.sh"

# validate_numeric - Ensure value is numeric, fallback to 0 if not
# Args:
#   $1: Value to validate
# Returns: The value if numeric, "0" otherwise
validate_numeric() {
	local val="$1"
	if [[ "$val" =~ ^[0-9]+\.?[0-9]*$ ]]; then
		echo "$val"
	else
		echo "0"
	fi
}

# extract_count - Extract a test count from pytest output
# Handles multiple output formats including standard pytest and plugin variations.
#
# Args:
#   $1: Output text to search
#   $2: Status name (e.g., "passed", "failed", "skipped")
#
# Returns: The count or "0" if not found
extract_count() {
	local output="$1"
	local status="$2"
	local count

	# Try standard "N status" format (e.g., "10 passed")
	count=$(echo "$output" | grep -oE "[0-9]+ $status" | grep -oE '[0-9]+' | head -1 || true)
	if [ -n "$count" ]; then
		echo "$count"
		return
	fi

	# Try "status: N" format (some plugins use this, case-insensitive)
	count=$(echo "$output" | grep -ioE "$status: *[0-9]+" | grep -oE '[0-9]+' | head -1 || true)
	if [ -n "$count" ]; then
		echo "$count"
		return
	fi

	# Try "STATUS: N" uppercase format
	local upper_status
	upper_status=$(echo "$status" | tr '[:lower:]' '[:upper:]')
	count=$(echo "$output" | grep -oE "$upper_status: *[0-9]+" | grep -oE '[0-9]+' | head -1 || true)
	if [ -n "$count" ]; then
		echo "$count"
		return
	fi

	echo "0"
}

# Parse arguments
INPUT_FILE="${1:-}"
OUTPUT_FILE="${2:-test-summary.json}"

# If no input file, try to extract from environment or use defaults
if [ -z "$INPUT_FILE" ] || [ ! -f "$INPUT_FILE" ]; then
	# Use environment variables if available (set by run-tests.sh)
	PASSED="${TEST_PASSED:-0}"
	FAILED="${TEST_FAILED:-0}"
	SKIPPED="${TEST_SKIPPED:-0}"
	ERRORS="${TEST_ERRORS:-0}"
	TOTAL="${TEST_TOTAL:-0}"
	DURATION="${TEST_DURATION:-0}"
else
	# Parse test output to extract summary
	OUTPUT=$(cat "$INPUT_FILE")

	# Try to extract from lintro table format first
	# Format: | 🧪 pytest | ❌ FAIL   | 3253     | 2        | 26        | 3281    | 82.06s     |
	# Also matches simpler format: | pytest | PASS | ... |
	LINTRO_LINE=$(echo "$OUTPUT" | grep -E '^\|.*pytest' | tail -1 || echo "")

	if [ -n "$LINTRO_LINE" ]; then
		# Parse lintro table format (pipe-separated columns)
		# Columns: Tool | Status | Passed | Failed | Skipped | Total | Duration
		PASSED=$(echo "$LINTRO_LINE" | awk -F'|' '{gsub(/[^0-9]/, "", $4); print $4}')
		FAILED=$(echo "$LINTRO_LINE" | awk -F'|' '{gsub(/[^0-9]/, "", $5); print $5}')
		SKIPPED=$(echo "$LINTRO_LINE" | awk -F'|' '{gsub(/[^0-9]/, "", $6); print $6}')
		TOTAL=$(echo "$LINTRO_LINE" | awk -F'|' '{gsub(/[^0-9]/, "", $7); print $7}')
		DURATION=$(echo "$LINTRO_LINE" | awk -F'|' '{gsub(/[^0-9.]/, "", $8); print $8}')
		ERRORS="0"
	else
		# Fallback: Extract counts from standard pytest output format
		# Uses extract_count helper to handle format variations (plugins, etc.)
		PASSED=$(extract_count "$OUTPUT" "passed")
		FAILED=$(extract_count "$OUTPUT" "failed")
		SKIPPED=$(extract_count "$OUTPUT" "skipped")
		# Handle "error" or "errors" variants
		ERRORS=$(echo "$OUTPUT" | grep -oE '[0-9]+ errors?' | grep -oE '[0-9]+' | head -1 || echo "0")
		DURATION=$(echo "$OUTPUT" | grep -oE 'in [0-9]+\.[0-9]+s' | grep -oE '[0-9]+\.[0-9]+' | tail -1 || echo "0")

		# Calculate total
		TOTAL=$((PASSED + FAILED + SKIPPED + ERRORS))
	fi

	# Set defaults for empty values
	PASSED="${PASSED:-0}"
	FAILED="${FAILED:-0}"
	SKIPPED="${SKIPPED:-0}"
	ERRORS="${ERRORS:-0}"
	TOTAL="${TOTAL:-0}"
	DURATION="${DURATION:-0}"
fi

# Also extract coverage details from coverage.xml if available
COVERAGE_LINES_COVERED="0"
COVERAGE_LINES_TOTAL="0"
COVERAGE_LINES_MISSING="0"
COVERAGE_FILES="0"
COVERAGE_PERCENTAGE="0"

if [ -f "coverage.xml" ]; then
	# Extract line-rate and convert to percentage
	LINE_RATE=$(sed -n 's/.*line-rate="\([^"]*\)".*/\1/p' coverage.xml | head -n1)
	LINE_RATE="${LINE_RATE:-0}"
	COVERAGE_PERCENTAGE=$(awk -v lr="$LINE_RATE" 'BEGIN { printf "%.1f", lr * 100 }')

	# Extract lines covered and valid from coverage.xml
	LINES_COVERED=$(sed -n 's/.*lines-covered="\([^"]*\)".*/\1/p' coverage.xml | head -n1)
	LINES_VALID=$(sed -n 's/.*lines-valid="\([^"]*\)".*/\1/p' coverage.xml | head -n1)

	COVERAGE_LINES_COVERED="${LINES_COVERED:-0}"
	COVERAGE_LINES_TOTAL="${LINES_VALID:-0}"
	COVERAGE_LINES_MISSING=$((COVERAGE_LINES_TOTAL - COVERAGE_LINES_COVERED))

	# Count files (number of <class> elements)
	COVERAGE_FILES=$(grep -c '<class ' coverage.xml 2>/dev/null || echo "0")
fi

# Validate all values are numeric before JSON generation
PASSED=$(validate_numeric "$PASSED")
FAILED=$(validate_numeric "$FAILED")
SKIPPED=$(validate_numeric "$SKIPPED")
ERRORS=$(validate_numeric "$ERRORS")
TOTAL=$(validate_numeric "$TOTAL")
DURATION=$(validate_numeric "$DURATION")
COVERAGE_PERCENTAGE=$(validate_numeric "$COVERAGE_PERCENTAGE")
COVERAGE_LINES_COVERED=$(validate_numeric "$COVERAGE_LINES_COVERED")
COVERAGE_LINES_TOTAL=$(validate_numeric "$COVERAGE_LINES_TOTAL")
COVERAGE_LINES_MISSING=$(validate_numeric "$COVERAGE_LINES_MISSING")
COVERAGE_FILES=$(validate_numeric "$COVERAGE_FILES")

# Generate JSON output
# Note: JSON uses single space after colon ("key": value) for compatibility
# with grep-based parsers in coverage-pr-comment.sh and similar scripts.
cat >"$OUTPUT_FILE" <<EOF
{
  "tests": {
    "passed": $PASSED,
    "failed": $FAILED,
    "skipped": $SKIPPED,
    "errors": $ERRORS,
    "total": $TOTAL,
    "duration": $DURATION
  },
  "coverage": {
    "percentage": $COVERAGE_PERCENTAGE,
    "lines_covered": $COVERAGE_LINES_COVERED,
    "lines_total": $COVERAGE_LINES_TOTAL,
    "lines_missing": $COVERAGE_LINES_MISSING,
    "files": $COVERAGE_FILES
  }
}
EOF

# Output summary unless quiet mode is enabled
if [ "$QUIET" -eq 0 ]; then
	log_success "Test summary extracted to $OUTPUT_FILE"
	echo "  Tests: $PASSED passed, $FAILED failed, $SKIPPED skipped, $TOTAL total (${DURATION}s)"
	echo "  Coverage: ${COVERAGE_PERCENTAGE}% (${COVERAGE_LINES_COVERED}/${COVERAGE_LINES_TOTAL} lines, ${COVERAGE_FILES} files)"
fi
