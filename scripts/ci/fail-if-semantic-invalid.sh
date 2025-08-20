#!/usr/bin/env bash
set -euo pipefail

# fail-if-semantic-invalid.sh
# Exit with failure if provided OK flag is not 'true'.
# Intended for use after semantic PR title validation.
#
# Usage:
#   OK=<true|false> scripts/ci/fail-if-semantic-invalid.sh

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Fail the step when the semantic validation reported ok != true.

Usage:
  OK=<true|false> scripts/ci/fail-if-semantic-invalid.sh
EOF
  exit 0
fi

OK_VALUE="${OK:-}"
if [[ -z "${OK_VALUE}" ]]; then
  echo "OK env var is required (expected 'true' or 'false')" >&2
  exit 2
fi

if [[ "${OK_VALUE}" != "true" ]]; then
  echo "PR title does not follow Conventional Commits." >&2
  exit 1
fi

echo "Semantic validation ok=true; continuing."


