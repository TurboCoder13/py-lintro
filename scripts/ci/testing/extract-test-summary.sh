#!/usr/bin/env bash
set -euo pipefail

# extract-test-summary.sh - Extract test summary from pytest output
#
# Parses the test output to extract passed/failed/skipped/total/duration
# and saves to a JSON file for use in PR comments.

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
	cat <<'EOF'
Usage: extract-test-summary.sh <test-output-file> <output-json-file>

Extract test summary from pytest output and save to JSON.

Arguments:
  test-output-file   Path to file containing pytest output
  output-json-file   Path to write the JSON summary

Example:
  ./extract-test-summary.sh test-output.log test-summary.json
EOF
	exit 0
fi

# Source shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../utils/utils.sh disable=SC1091
source "$SCRIPT_DIR/../../utils/utils.sh"

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
	LINTRO_LINE=$(echo "$OUTPUT" | grep -E '^\| .* pytest' | tail -1 || echo "")

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
		PASSED=$(echo "$OUTPUT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | head -1 || echo "0")
		FAILED=$(echo "$OUTPUT" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' | head -1 || echo "0")
		SKIPPED=$(echo "$OUTPUT" | grep -oE '[0-9]+ skipped' | grep -oE '[0-9]+' | head -1 || echo "0")
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
	LINES_COVERED=$(sed -n 's/.*lines-covered="\([^"]*\)".*/\1/p' coverage.xml | head -n1 || echo "0")
	LINES_VALID=$(sed -n 's/.*lines-valid="\([^"]*\)".*/\1/p' coverage.xml | head -n1 || echo "0")

	COVERAGE_LINES_COVERED="${LINES_COVERED:-0}"
	COVERAGE_LINES_TOTAL="${LINES_VALID:-0}"
	COVERAGE_LINES_MISSING=$((COVERAGE_LINES_TOTAL - COVERAGE_LINES_COVERED))

	# Count files (number of <class> elements)
	COVERAGE_FILES=$(grep -c '<class ' coverage.xml 2>/dev/null || echo "0")
fi

# Generate JSON output
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

log_success "Test summary extracted to $OUTPUT_FILE"
echo "  Tests: $PASSED passed, $FAILED failed, $SKIPPED skipped, $TOTAL total (${DURATION}s)"
echo "  Coverage: ${COVERAGE_PERCENTAGE}% (${COVERAGE_LINES_COVERED}/${COVERAGE_LINES_TOTAL} lines, ${COVERAGE_FILES} files)"
