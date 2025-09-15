#!/usr/bin/env bash
set -euo pipefail

# auto-tag-configure-auth.sh
# Configure git remote auth for tag push using a provided token.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Configure git remote auth for tag push.

Env:
  RELEASE_TOKEN   GitHub App installation token (required)
  REPOSITORY      owner/repo (required)

EOF
  exit 0
fi

: "${RELEASE_TOKEN:?RELEASE_TOKEN not set}"
: "${REPOSITORY:?REPOSITORY not set}"

git remote set-url origin "https://x-access-token:${RELEASE_TOKEN}@github.com/${REPOSITORY}.git"
git config user.name "release-bot"
git config user.email "releases@users.noreply.github.com"

#!/usr/bin/env bash
set -euo pipefail

# auto-tag-configure-auth.sh
# Configure git remote auth using a provided installation token.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Configure git remote with a token for authenticated push.

Env:
  RELEASE_TOKEN   GitHub App installation token or PAT
  REPOSITORY      owner/repo (defaults to GITHUB_REPOSITORY)

EOF
  exit 0
fi

REPO="${REPOSITORY:-${GITHUB_REPOSITORY:-}}"
TOKEN="${RELEASE_TOKEN:-}"

if [[ -z "$REPO" || -z "$TOKEN" ]]; then
  echo "Missing REPOSITORY or RELEASE_TOKEN" >&2
  exit 1
fi

git remote set-url origin "https://x-access-token:${TOKEN}@github.com/${REPO}.git"
echo "Configured authenticated remote for ${REPO}" >&2


