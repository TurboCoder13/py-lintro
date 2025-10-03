#!/usr/bin/env bash
set -euo pipefail

# configure-git-user.sh
# Configure git user.name, user.email, and mark workspace safe.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Configure git identity and safe.directory.

Env:
  GIT_USER   User name (required)
  GIT_EMAIL  User email (required)

EOF
  exit 0
fi

: "${GIT_USER:?GIT_USER not set}"
: "${GIT_EMAIL:?GIT_EMAIL not set}"

git config --global user.name "${GIT_USER}"
git config --global user.email "${GIT_EMAIL}"
git config --global --add safe.directory "${GITHUB_WORKSPACE:-$PWD}"
git config --global commit.gpgsign false


