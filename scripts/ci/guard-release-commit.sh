#!/usr/bin/env bash
set -euo pipefail

# guard-release-commit.sh
# Set ok=true in GITHUB_OUTPUT if last commit subject starts with 'chore(release):'

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Guard that last commit message is a release bump.

Usage:
  scripts/ci/guard-release-commit.sh

Writes ok=true|false to $GITHUB_OUTPUT.
EOF
  exit 0
fi

msg=$(git log -1 --pretty=%s)
echo "last: $msg"
ok=false
if echo "$msg" | grep -Eq '^chore\(release\):'; then
  ok=true
fi

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "ok=$ok" >> "$GITHUB_OUTPUT"
else
  echo "ok=$ok"
fi

