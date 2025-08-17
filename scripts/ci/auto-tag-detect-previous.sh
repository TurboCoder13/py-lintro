#!/usr/bin/env bash
set -euo pipefail

# auto-tag-detect-previous.sh
# Determine previous version from prior commit's pyproject.toml

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  echo "Usage: scripts/ci/auto-tag-detect-previous.sh"
  echo ""
  echo "Detect the previous project version from HEAD^:pyproject.toml and write"
  echo "'version=X.Y.Z' (or empty) to GITHUB_OUTPUT."
  exit 0
fi

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


