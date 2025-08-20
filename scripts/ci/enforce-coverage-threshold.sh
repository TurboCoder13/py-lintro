#!/usr/bin/env bash
set -euo pipefail

# enforce-coverage-threshold.sh
# Enforce a minimum coverage percentage. Fails if below threshold.
# Usage:
#   scripts/ci/enforce-coverage-threshold.sh [PERCENTAGE] [THRESHOLD]
# Env:
#   COVERAGE_PERCENTAGE  Optional. Used if PERCENTAGE arg not given
#   THRESHOLD            Optional. Default: 80

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Enforce a minimum coverage percentage.

Usage:
  scripts/ci/enforce-coverage-threshold.sh [PERCENTAGE] [THRESHOLD]

Arguments:
  PERCENTAGE  The coverage percentage (e.g., 81.2). If omitted, reads from
              COVERAGE_PERCENTAGE env var or computes from coverage.xml.
  THRESHOLD   Minimum required coverage (default: 80)

Exit status:
  0 if PERCENTAGE >= THRESHOLD; 1 otherwise
EOF
  exit 0
fi

PCT_INPUT=${1:-}
THRESHOLD=${2:-${THRESHOLD:-80}}

percentage() {
  local pct
  if [[ -n "$PCT_INPUT" ]]; then
    pct="$PCT_INPUT"
  elif [[ -n "${COVERAGE_PERCENTAGE:-}" ]]; then
    pct="$COVERAGE_PERCENTAGE"
  elif [[ -f coverage.xml ]]; then
    pct=$(python3 scripts/utils/extract-coverage.py | awk -F= '/^percentage=/{print $2; exit}')
  else
    pct="0.0"
  fi
  echo "$pct"
}

PCT=$(percentage)
awk -v p="$PCT" -v t="$THRESHOLD" 'BEGIN{ exit (p>=t)?0:1 }'

echo "Coverage threshold satisfied: ${PCT}% >= ${THRESHOLD}%"

