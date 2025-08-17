#!/usr/bin/env bash
set -euo pipefail

# ci-auto-fix.sh
# Auto-format using lintro inside Docker and push changes back to PR branch

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  echo "Usage: scripts/ci/ci-auto-fix.sh"
  echo ""
  echo "Run 'lintro format' inside Docker and push fixes back to PR branch."
  echo "Environment:"
  echo "  HEAD_REF            PR head ref (required for pull_request)"
  echo "  GITHUB_EVENT_NAME   GitHub event name (pull_request or push)"
  exit 0
fi

HEAD_REF=${HEAD_REF:-}
GITHUB_EVENT_NAME=${GITHUB_EVENT_NAME:-}

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

docker run --rm \
  -v "$PWD:/code" \
  -w /code \
  py-lintro:latest \
  lintro format . --output-format grid || true

if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -m "style: auto-format via Lintro"
  if [ "$GITHUB_EVENT_NAME" = "pull_request" ]; then
    git push origin HEAD:"$HEAD_REF"
  else
    git push
  fi
  echo "Auto-format changes pushed back to PR branch."
else
  echo "No changes after formatting."
fi


