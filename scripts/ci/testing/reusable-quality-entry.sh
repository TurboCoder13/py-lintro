#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Run quality gate in reusable workflow: install tools, check, export version.
EOF
	exit 0
fi

./scripts/utils/install-tools.sh --local
echo "$HOME/.local/bin" >>"$GITHUB_PATH"

# Verify tool versions are synchronized between package.json and _tool_versions.py
echo "Verifying tool version synchronization..."
python scripts/ci/verify-tool-version-sync.py

uv run lintro check . --output-format grid

python scripts/utils/extract-version.py | tee ver.txt
cat ver.txt >>"$GITHUB_OUTPUT"
