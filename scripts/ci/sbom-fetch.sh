#!/usr/bin/env bash
set -euo pipefail

# sbom-fetch.sh
# Fetch repository SBOM graph via bomctl using the GH token.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Fetch repository SBOM via bomctl and export via sbom-generate.sh

Usage:
  scripts/ci/sbom-fetch.sh [--format cyclonedx-1.6 --format spdx-2.3]

Notes:
  - Requires bomctl binary installed on PATH
  - Uses GITHUB_TOKEN if present
EOF
  exit 0
fi

: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY not set}"

repo_url="https://github.com/${GITHUB_REPOSITORY}"

set -e
bomctl fetch "${repo_url}"
bomctl merge --alias "project" --name "py-lintro-sbom" "${repo_url}"

# Pass through any format args to sbom-generate.sh
bash scripts/ci/sbom-generate.sh --skip-fetch --name "py-lintro-sbom" --alias project "$@"


