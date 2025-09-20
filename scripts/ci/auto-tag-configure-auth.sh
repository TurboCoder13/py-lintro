#!/usr/bin/env bash
set -euo pipefail

# auto-tag-configure-auth.sh
# Configure git remote with a token for authenticated tag pushes and set
# a safe default git identity for tagging operations.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Configure git remote with a token for authenticated tag pushes.

Env:
  RELEASE_TOKEN   GitHub App installation token or PAT (required)
  REPOSITORY      owner/repo (defaults to GITHUB_REPOSITORY)
  GIT_USER        git user.name (default: release-bot)
  GIT_EMAIL       git user.email (default: releases@users.noreply.github.com)
EOF
  exit 0
fi

REPO="${REPOSITORY:-${GITHUB_REPOSITORY:-}}"
TOKEN="${RELEASE_TOKEN:-}"
GIT_USER_NAME="${GIT_USER:-release-bot}"
GIT_USER_EMAIL="${GIT_EMAIL:-releases@users.noreply.github.com}"

if [[ -z "${REPO}" || -z "${TOKEN}" ]]; then
  echo "Missing REPOSITORY/GITHUB_REPOSITORY or RELEASE_TOKEN" >&2
  exit 1
fi

git remote set-url origin "https://x-access-token:${TOKEN}@github.com/${REPO}.git"
git config user.name "${GIT_USER_NAME}"
git config user.email "${GIT_USER_EMAIL}"

echo "Configured authenticated remote for ${REPO} with user '${GIT_USER_NAME}'" >&2
