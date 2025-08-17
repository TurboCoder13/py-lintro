#!/usr/bin/env bash
set -euo pipefail

# auto-tag-create-push-tag.sh
# Create and push annotated tag using TAG env var

TAG=${TAG:-}
if [ -z "$TAG" ]; then
  echo "TAG is required" >&2
  exit 2
fi

git config user.name "github-actions"
git config user.email "github-actions@github.com"
git tag -a "$TAG" -m "Release $TAG"
git push origin "$TAG"


