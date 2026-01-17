#!/usr/bin/env bash
# git-commit-push.sh
# Stage, commit, and push changes with github-actions[bot] identity

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../utils/utils.sh
source "$SCRIPT_DIR/../utils/utils.sh"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Stage, commit, and push changes to git.

Usage: git-commit-push.sh <file-pattern> <commit-message>

Arguments:
  file-pattern    Git add pattern (e.g., "Formula/lintro.rb" or ".")
  commit-message  Commit message

Options:
  --skip-if-empty  Exit 0 if there are no changes (default: error)

Env:
  WORKING_DIR  Directory to run in (default: current directory)

Examples:
  git-commit-push.sh "Formula/lintro.rb" "Update lintro to 1.0.0"
  git-commit-push.sh "." "Auto-fix formatting" --skip-if-empty
EOF
	exit 0
fi

FILE_PATTERN="${1:?File pattern is required}"
COMMIT_MESSAGE="${2:?Commit message is required}"
SKIP_IF_EMPTY="${3:-}"
WORKING_DIR="${WORKING_DIR:-.}"

cd "$WORKING_DIR"

# Configure git identity
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"

log_info "Staging changes: $FILE_PATTERN"
git add "$FILE_PATTERN"

# Check if there are staged changes
if git diff --staged --quiet; then
	if [[ "$SKIP_IF_EMPTY" == "--skip-if-empty" ]]; then
		log_info "No changes to commit, skipping"
		exit 0
	else
		log_warning "No changes to commit"
		exit 0
	fi
fi

log_info "Committing changes"
git commit -m "$COMMIT_MESSAGE"

log_info "Pushing to remote"
git push

log_success "Changes pushed successfully"
