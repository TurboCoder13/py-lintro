#!/usr/bin/env bash
set -euo pipefail

# ci-auto-fix.sh
# Auto-format using lintro inside Docker and push changes back to PR branch

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


