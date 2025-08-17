#!/usr/bin/env bash
set -euo pipefail

# auto-tag-read-version.sh
# Read version from pyproject and export to GITHUB_OUTPUT as version=<x.y.z>

ver=$(uv run python scripts/utils/extract-version.py | sed 's/^version=//')
echo "Detected version: $ver"
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  echo "version=$ver" >> "$GITHUB_OUTPUT"
else
  echo "GITHUB_OUTPUT is not set; printing to stdout"
  echo "version=$ver"
fi


