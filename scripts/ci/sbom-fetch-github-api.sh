#!/usr/bin/env bash
set -euo pipefail

# sbom-fetch-github-api.sh
# Fetch repository SBOM using GitHub REST API instead of bomctl fetch.
# This approach uses GitHub's native dependency graph SBOM export.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Fetch repository SBOM via GitHub REST API and import via bomctl

Usage:
  scripts/ci/sbom-fetch-github-api.sh [--format cyclonedx-1.6 --format spdx-2.3]

Notes:
  - Requires GITHUB_TOKEN to be set
  - Requires gh CLI or curl
  - Falls back to local-only SBOM generation if fetch fails
EOF
  exit 0
fi

: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY not set}"
: "${GITHUB_TOKEN:?GITHUB_TOKEN not set}"

repo_url="https://github.com/${GITHUB_REPOSITORY}"
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

echo "[sbom-fetch] Fetching SBOM from GitHub Dependency Graph API..." >&2

# Try to fetch SBOM using GitHub REST API
# Format: /repos/{owner}/{repo}/dependency-graph/sbom
owner="${GITHUB_REPOSITORY%/*}"
repo="${GITHUB_REPOSITORY#*/}"

# Use gh CLI if available, otherwise curl
if command -v gh >/dev/null 2>&1; then
  echo "[sbom-fetch] Using gh CLI to fetch SBOM..." >&2
  if gh api "/repos/${owner}/${repo}/dependency-graph/sbom" > "${tmpdir}/github-sbom.json" 2>/dev/null; then
    echo "[sbom-fetch] Successfully fetched SBOM from GitHub" >&2
    
    # Import the fetched SBOM into bomctl
    if command -v bomctl >/dev/null 2>&1; then
      bomctl import --alias "github-deps" "${tmpdir}/github-sbom.json" || {
        echo "[sbom-fetch] Warning: Failed to import GitHub SBOM, continuing with local SBOM only" >&2
      }
    fi
  else
    echo "[sbom-fetch] Warning: Could not fetch SBOM from GitHub API (may not be available), continuing with local SBOM only" >&2
  fi
else
  echo "[sbom-fetch] gh CLI not available, skipping GitHub SBOM fetch" >&2
fi

# Generate SBOMs with provided formats
echo "[sbom-fetch] Generating SBOM artifacts..." >&2
bash scripts/ci/sbom-generate.sh --skip-fetch --name "py-lintro-sbom" --alias project "$@"



