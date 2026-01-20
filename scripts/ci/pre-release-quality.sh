#!/usr/bin/env bash
set -euo pipefail

# pre-release-quality.sh
# Run Lintro check with grid output.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Run Lintro checks prior to release.

Usage:
  scripts/ci/pre-release-quality.sh
EOF
	exit 0
fi

uv run lintro check . --output-format grid
