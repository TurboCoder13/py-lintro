#!/usr/bin/env bash
set -euo pipefail

# auto-tag-create-push-tag.sh
# Create and push annotated tag using TAG env var

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  echo "Usage: scripts/ci/auto-tag-create-push-tag.sh"
  echo ""
  echo "Create and push an annotated tag using TAG env variable."
  echo "Environment:"
  echo "  TAG  Required. Version string to tag (e.g., 0.1.1)"
  exit 0
fi

TAG=${TAG:-}
if [ -z "$TAG" ]; then
  echo "TAG is required" >&2
  exit 2
fi

git config user.name "github-actions"
git config user.email "github-actions@github.com"
git tag -a "$TAG" -m "Release $TAG"
git push origin "$TAG"


