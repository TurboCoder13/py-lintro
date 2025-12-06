#!/usr/bin/env bash
set -euo pipefail

# validate-action-pinning.sh
# Scan .github/workflows for non-pinned 'uses:' references.
# Exits with 0 by default (non-blocking). Set ENFORCE=1 to fail on offenders.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Validate GitHub Action pinning to commit SHAs.

Usage:
  scripts/ci/validate-action-pinning.sh

Env:
  ENFORCE=1  Fail the script if non-pinned actions are found (default: 0)
EOF
  exit 0
fi

echo "Scanning for non-pinned GitHub Actions..."
offenders=0
while IFS= read -r line; do
  file="${line%%:*}"
  rest="${line#*:}"
  uses_line="${rest#*:}"
  # Ignore local/composite actions and docker:// references
  if echo "$uses_line" | grep -Eq '^\s*uses:\s*(\./|docker://)'; then
    continue
  fi
  # Extract the reference after '@' up to whitespace or end
  ref=$(echo "$uses_line" | awk -F'@' '{print $2}' | awk '{print $1}')
  # Normalize and validate reference
  ref=$(echo "$ref" | tr -d '\r\n\t ')
  # Accept commit SHAs (40 hex, case-insensitive) or expressions (matrix/inputs)
  if echo "$ref" | grep -Eq '^[A-Fa-f0-9]{40}$|^\$\{\{'; then
    continue
  fi
  # Accept semantic version tags for internal TurboCoder13/py-lintro actions
  # Internal actions use semantic versioning (@v1, @v1.0.0) instead of SHA pinning
  if echo "$uses_line" | grep -Eq 'TurboCoder13/py-lintro/.github/(actions|workflows)' && \
     echo "$ref" | grep -Eq '^v[0-9]+(\.[0-9]+(\.[0-9]+)?)?$'; then
    continue
  fi
  echo "Non-pinned action in $file: $uses_line"
  offenders=$((offenders+1))
done < <(grep -RIn "^\s*uses:\s*[^#]" .github/workflows | sed 's/\t/ /g')

echo "Found $offenders non-pinned action reference(s)."
if [[ "${ENFORCE:-0}" == "1" && "$offenders" -gt 0 ]]; then
  echo "Failing due to ENFORCE=1 and offenders present" >&2
  exit 1
fi

