#!/usr/bin/env bash
set -euo pipefail

# enforce-coverage-threshold.sh
# Enforce a minimum coverage percentage. Fails if below threshold.
# Usage:
#   scripts/ci/enforce-coverage-threshold.sh [PERCENTAGE] [THRESHOLD]
# Env:
#   COVERAGE_PERCENTAGE  Optional. Used if PERCENTAGE arg not given
#   THRESHOLD            Optional. Default: 80

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../utils/utils.sh
source "$SCRIPT_DIR/../../utils/utils.sh"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    cat <<'EOF'
Enforce a minimum coverage percentage.

Usage:
  enforce-coverage-threshold.sh [PERCENTAGE] [THRESHOLD]

Arguments:
  PERCENTAGE  The coverage percentage (e.g., 81.2). If omitted, reads from
              COVERAGE_PERCENTAGE env var or computes from coverage.xml.
  THRESHOLD   Minimum required coverage (default: 80)

Exit status:
  0 if PERCENTAGE >= THRESHOLD; 1 otherwise
EOF
    exit 0
fi

PCT_INPUT="${1:-}"
THRESHOLD="${2:-${THRESHOLD:-80}}"

# Get coverage percentage from argument, environment, or coverage.xml
get_pct() {
    local pct
    if [[ -n "$PCT_INPUT" ]]; then
        pct="$PCT_INPUT"
    elif [[ -n "${COVERAGE_PERCENTAGE:-}" ]]; then
        pct="$COVERAGE_PERCENTAGE"
    else
        # Use shared get_coverage_percentage function from utils.sh
        pct=$(get_coverage_percentage "coverage.xml")
    fi
    echo "$pct"
}

PCT=$(get_pct)

if awk -v p="$PCT" -v t="$THRESHOLD" 'BEGIN{ exit (p>=t)?0:1 }'; then
    log_success "Coverage threshold satisfied: ${PCT}% >= ${THRESHOLD}%"
else
    log_error "Coverage threshold NOT satisfied: ${PCT}% < ${THRESHOLD}%"
    exit 1
fi

