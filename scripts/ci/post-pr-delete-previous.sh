#!/usr/bin/env bash
set -euo pipefail

# post-pr-delete-previous.sh
# Delete previous PR comments by marker using the project Python utility.
#
# Usage:
#   scripts/ci/post-pr-delete-previous.sh <marker>
#
# Environment (required):
#   GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Delete previous PR comments by marker.

Usage:
  scripts/ci/post-pr-delete-previous.sh <marker>

Environment:
  GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER must be set (GitHub Actions provides them).
EOF
  exit 0
fi

MARKER="${1:-}"
if [[ -z "${MARKER}" ]]; then
  echo "Marker argument is required" >&2
  exit 2
fi

# Run deletion but do not fail the job if nothing to delete or API transient error
if ! uv run python scripts/utils/delete-previous-lintro-comments.py "${MARKER}"; then
  echo "No previous comments to delete or deletion not required; continuing."
fi


