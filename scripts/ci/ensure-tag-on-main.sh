#!/usr/bin/env bash
set -euo pipefail

# ensure-tag-on-main.sh
# Verify that the dereferenced tag commit is an ancestor of origin/main.
# Requires fetch of origin/main.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Ensure tag points at a commit on main.

Usage:
  scripts/ci/ensure-tag-on-main.sh

Exits non-zero if the tag's commit is not an ancestor of origin/main.
EOF
  exit 0
fi

git fetch --no-tags origin main:refs/remotes/origin/main

TAG_COMMIT=$(git rev-parse "$GITHUB_REF^{}")
echo "Tag $GITHUB_REF_NAME -> $TAG_COMMIT"
if git merge-base --is-ancestor "$TAG_COMMIT" origin/main; then
  echo "Tag commit is on main"
else
  echo "Tag commit is not on main; aborting publish" >&2
  exit 1
fi

