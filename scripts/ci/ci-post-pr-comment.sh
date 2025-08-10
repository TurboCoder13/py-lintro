#!/bin/bash

# CI Post PR Comment Script
# Handles posting comments to PRs using GitHub API

set -e

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [--help] [COMMENT_FILE]"
    echo ""
    echo "CI Post PR Comment Script"
    echo "Handles posting comments to PRs using GitHub API."
    echo ""
    echo "Arguments:"
    echo "  COMMENT_FILE    Path to comment file (default: pr-comment.txt)"
    echo ""
    echo "This script:"
    echo "  - Posts comments to GitHub PRs using GitHub API"
    echo "  - Uses Node.js GitHub script for API interaction"
    echo "  - Handles PR context validation"
    echo ""
    echo "This script is designed to be run in GitHub Actions CI environment."
    exit 0
fi

# Source shared utilities
source "$(dirname "$0")/../utils/utils.sh"

# Check if we're in a PR context
if ! is_pr_context; then
    log_info "Not in a PR context, skipping comment posting"
    exit 0
fi

# Get the comment file from argument
COMMENT_FILE="${1:-pr-comment.txt}"

if [ ! -f "$COMMENT_FILE" ]; then
    log_error "Comment file $COMMENT_FILE not found"
    exit 1
fi

log_info "Posting PR comment from $COMMENT_FILE"

# Post PR comment using GitHub CLI if available, otherwise fallback to API via curl
if command -v gh &> /dev/null; then
    gh api repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments \
      -f body@"$COMMENT_FILE"
    log_success "PR comment posted successfully via gh"
else
    log_info "gh not found, using curl to post PR comment"
    # Fallback without requiring jq: safely JSON-encode body using Python
    JSON_BODY=$(python - <<'PY'
import json, sys
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    body = f.read()
print(json.dumps({"body": body}))
PY
"$COMMENT_FILE")
    curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" \
         -H "Accept: application/vnd.github+json" \
         -H "X-GitHub-Api-Version: 2022-11-28" \
         -X POST \
         -d "$JSON_BODY" \
         "https://api.github.com/repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments"
    log_success "PR comment posted successfully via curl"
fi