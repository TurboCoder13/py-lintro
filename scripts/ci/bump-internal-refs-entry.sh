#!/usr/bin/env bash
set -euo pipefail

# bump-internal-refs-entry.sh
# Wrapper to call bump-internal-refs.sh with a SHA from input or default to GITHUB_SHA.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Wrapper around bump-internal-refs.sh that chooses a SHA.

Env:
  SHA_INPUT   Optional; if set, used as the target SHA
  GITHUB_SHA  Used if SHA_INPUT is empty
EOF
  exit 0
fi

sha_input="${SHA_INPUT:-}"

if [[ -n "${sha_input}" ]]; then
  scripts/ci/bump-internal-refs.sh "${sha_input}"
else
  scripts/ci/bump-internal-refs.sh "${GITHUB_SHA:-}"
fi


