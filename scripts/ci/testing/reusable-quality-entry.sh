#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Run quality gate in reusable workflow: install tools, format, check, export version.
EOF
	exit 0
fi

./scripts/utils/install-tools.sh --local
echo "$HOME/.local/bin" >>"$GITHUB_PATH"

uv run lintro format . --output-format grid
uv run lintro check . --output-format grid

python scripts/utils/extract-version.py | tee ver.txt
cat ver.txt >>"$GITHUB_OUTPUT"
