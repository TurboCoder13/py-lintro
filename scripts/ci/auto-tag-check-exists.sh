#!/usr/bin/env bash
set -euo pipefail

# auto-tag-check-exists.sh
# Determine if a given tag exists in the current git repo and export result.
#
# Usage:
#   scripts/ci/auto-tag-check-exists.sh [TAG]
#
# Inputs:
#   - First positional arg TAG (optional)
#   - Or environment variable TAG (preferred when used in GitHub Actions)
#
# Outputs:
#   - Writes exists=true|false to $GITHUB_OUTPUT when set

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Check whether a given git tag exists and write exists=true|false to GITHUB_OUTPUT.

Usage:
  scripts/ci/auto-tag-check-exists.sh [TAG]

Environment:
  TAG  Optional. Tag to check (e.g., v0.1.1). When absent, first positional arg
       is used. One of them must be provided.
EOF
  exit 0
fi

TAG_TO_CHECK="${TAG:-${1:-}}"
if [[ -z "${TAG_TO_CHECK}" ]]; then
  echo "Tag is required (use TAG env or pass as argument)" >&2
  exit 2
fi

if git rev-parse "${TAG_TO_CHECK}" >/dev/null 2>&1; then
  result="true"
else
  result="false"
fi

echo "exists=${result}"
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "exists=${result}" >> "${GITHUB_OUTPUT}"
fi


