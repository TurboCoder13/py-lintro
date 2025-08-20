#!/usr/bin/env bash
set -euo pipefail

# Bump same-repo action/workflow pinned refs to a given SHA (defaults to HEAD)
#
# Replaces occurrences of:
#   TurboCoder13/py-lintro/.github/actions/<name>@<sha>
#   TurboCoder13/py-lintro/.github/workflows/<file>@<sha>
# in all workflow files under .github/workflows/.
#
# Usage:
#   scripts/ci/bump-internal-refs.sh [<sha>]
#   scripts/ci/bump-internal-refs.sh --help

show_help() {
  cat <<'USAGE'
Usage: scripts/ci/bump-internal-refs.sh [<sha>]

Bump same-repo GitHub Actions and reusable workflow references to a pinned SHA.

Arguments:
  <sha>   Optional full-length commit SHA to pin. Defaults to current HEAD.

Examples:
  scripts/ci/bump-internal-refs.sh
  scripts/ci/bump-internal-refs.sh 0123456789abcdef0123456789abcdef01234567
USAGE
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

SHA_TO_PIN="${1:-}"
if [[ -z "${SHA_TO_PIN}" ]]; then
  SHA_TO_PIN="$(git rev-parse HEAD)"
fi

echo "Bumping internal action/workflow refs to SHA: ${SHA_TO_PIN}" >&2

# sed in-place portable helper (GNU/BSD)
sed_in_place() {
  if sed --version >/dev/null 2>&1; then
    sed -i "$@"
  else
    sed -i '' "$@"
  fi
}

while IFS= read -r -d '' file; do
  echo "Processing ${file}" >&2
  # Replace action refs
  sed_in_place -E \
    "s|(TurboCoder13/py-lintro/\.github/(actions|workflows)/[^@[:space:]]+@)[0-9a-f]{40}|\\1${SHA_TO_PIN}|g" \
    "$file"
done < <(find .github/workflows -type f -name '*.yml' -print0)

echo "Done. Changes (if any):" >&2
git status --porcelain .github/workflows || true


