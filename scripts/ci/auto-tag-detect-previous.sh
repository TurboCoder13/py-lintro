#!/usr/bin/env bash
set -euo pipefail

# auto-tag-detect-previous.sh
# Determine previous version from prior commit's pyproject.toml

git show HEAD^:pyproject.toml > /tmp/prev.toml || true
if [ -s /tmp/prev.toml ]; then
  uv run python scripts/utils/extract-version.py --file /tmp/prev.toml | tee prev.txt
  if [ -n "${GITHUB_OUTPUT:-}" ]; then
    cat prev.txt >> "$GITHUB_OUTPUT"
  fi
else
  if [ -n "${GITHUB_OUTPUT:-}" ]; then
    echo "version=" >> "$GITHUB_OUTPUT"
  else
    echo "version="
  fi
fi


