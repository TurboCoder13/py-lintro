#!/usr/bin/env bash
set -euo pipefail

# verify-tag-matches-pyproject.sh
# Compare current ref tag name with version in pyproject.toml (ignoring v-prefix).
# Exits non-zero if they do not match. Prints a helpful message.
#
# Usage:
#   scripts/ci/verify-tag-matches-pyproject.sh [--file PATH]
#
# Environment:
#   GITHUB_REF_NAME  Optional. Tag name provided by GitHub Actions (e.g., v0.1.1)

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Verify that the pushed tag matches the version in pyproject.toml.

Usage:
  scripts/ci/verify-tag-matches-pyproject.sh [--file PATH]

Options:
  --file PATH   Path to TOML file (default: pyproject.toml)
EOF
  exit 0
fi

FILE="pyproject.toml"
if [[ "${1:-}" == "--file" && -n "${2:-}" ]]; then
  FILE="${2}"
fi

if [[ ! -f "${FILE}" ]]; then
  echo "File not found: ${FILE}" >&2
  exit 2
fi

ver_line=$(uv run python scripts/utils/extract-version.py --file "${FILE}")
echo "${ver_line}"
version="${ver_line#version=}"

tag="${GITHUB_REF_NAME:-}"
if [[ -z "${tag}" ]]; then
  echo "GITHUB_REF_NAME not set; cannot determine tag" >&2
  exit 2
fi

tag_stripped="${tag#v}"
echo "pyproject version: ${version} / tag: ${tag} (stripped: ${tag_stripped})"

if [[ "${version}" != "${tag_stripped}" ]]; then
  echo "Version mismatch: pyproject=${version} tag=${tag}" >&2
  exit 1
fi


