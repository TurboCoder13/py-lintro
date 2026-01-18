#!/usr/bin/env bash
set -euo pipefail

# Normalize all ASCII art files to a standard size.
# Usage:
#   ./scripts/local/normalize-ascii-art.sh [WIDTH] [HEIGHT]
#   ./scripts/local/normalize-ascii-art.sh --help
# Defaults to 80x20 if not provided.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Normalize ASCII art files to a standard size.

Usage:
  scripts/local/normalize-ascii-art.sh [WIDTH] [HEIGHT]

Arguments:
  WIDTH   Target width in characters (default: 80)
  HEIGHT  Target height in lines (default: 20)

Examples:
  scripts/local/normalize-ascii-art.sh               # 80x20
  scripts/local/normalize-ascii-art.sh 100 24        # 100x24
EOF
	exit 0
fi

WIDTH=${1:-80}
HEIGHT=${2:-20}

uv run python -m lintro.utils.ascii_normalize_cli --width "${WIDTH}" --height "${HEIGHT}"
