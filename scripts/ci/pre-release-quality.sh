#!/usr/bin/env bash
set -euo pipefail

# pre-release-quality.sh
# Run Lintro format and check with grid output.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Run Lintro formatting and checks prior to release.

Usage:
  scripts/ci/pre-release-quality.sh
EOF
  exit 0
fi

uv run lintro format . --output-format grid
uv run lintro check . --output-format grid

