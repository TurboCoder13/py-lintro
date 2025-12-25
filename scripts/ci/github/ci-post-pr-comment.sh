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
source "$(dirname "$0")/../../utils/utils.sh"

# Check if we're in a PR context
if ! is_pr_context; then
    log_info "Not in a PR context, skipping comment posting"
    exit 0
fi

# Get the comment file from argument
COMMENT_FILE="${1:-pr-comment.txt}"

# Optional marker to enable merge-update behavior
MARKER="${MARKER:-}"

if [ ! -f "$COMMENT_FILE" ]; then
    log_error "Comment file $COMMENT_FILE not found"
    exit 1
fi

log_info "Preparing PR comment from $COMMENT_FILE"

# If a marker is provided, attempt to find an existing comment with that marker
# and merge the new content under a collapsed <details> section.
if [ -n "$MARKER" ]; then
    log_info "Marker provided; attempting to update existing comment in-place"
    # Fetch existing comments via gh API (fallback to curl if gh not available)
    if command -v gh &>/dev/null; then
        EXISTING_JSON=$(gh api repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments --paginate)
    else
        EXISTING_JSON=$(curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github+json" \
            -H "X-GitHub-Api-Version: 2022-11-28" \
            "https://api.github.com/repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments?per_page=100")
    fi

    # Extract the first comment id containing the marker (prefer latest by scanning from end)
    COMMENT_ID=$(echo "$EXISTING_JSON" | uv run python scripts/utils/find_comment_with_marker.py "$MARKER")

    if [ -n "$COMMENT_ID" ]; then
        log_info "Found existing comment with marker (id=$COMMENT_ID); preparing merged body"
        PREV_FILE=$(mktemp)
        NEW_FILE=$(mktemp)
        MERGED_FILE=$(mktemp)
        # Dump previous body
        echo "$EXISTING_JSON" | uv run python scripts/utils/extract_comment_body.py "$COMMENT_ID" > "$PREV_FILE"
        # Read new body
        cat "$COMMENT_FILE" > "$NEW_FILE"
        # Merge with Python utility and write to file to avoid argument length limits
        uv run python scripts/utils/merge_pr_comment.py "$MARKER" "$NEW_FILE" --previous-file "$PREV_FILE" > "$MERGED_FILE"
        # Post update via gh or curl
        if command -v gh &>/dev/null; then
            gh api repos/$GITHUB_REPOSITORY/issues/comments/$COMMENT_ID -X PATCH -F body=@"$MERGED_FILE" >/dev/null
            rm -f "$PREV_FILE" "$NEW_FILE" "$MERGED_FILE"
            log_success "PR comment updated successfully via gh api"
            exit 0
        else
            JSON_BODY=$(uv run python scripts/utils/json_encode_body.py < "$MERGED_FILE")
            curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" \
                 -H "Accept: application/vnd.github+json" \
                 -H "X-GitHub-Api-Version: 2022-11-28" \
                 -X PATCH \
                 -d "$JSON_BODY" \
                 "https://api.github.com/repos/$GITHUB_REPOSITORY/issues/comments/$COMMENT_ID" >/dev/null
            rm -f "$PREV_FILE" "$NEW_FILE" "$MERGED_FILE"
            log_success "PR comment updated successfully via curl"
            exit 0
        fi
    else
        log_info "No existing comment with marker; will create a new comment"
    fi
fi

log_info "Posting PR comment"

# Post PR comment using GitHub CLI if available, otherwise fallback to API via curl
if command -v gh &>/dev/null; then
    # Prefer high-level gh command when available (handles files and escaping)
    if gh pr comment "$PR_NUMBER" --body-file "$COMMENT_FILE" >/dev/null 2>&1; then
        log_success "PR comment posted successfully via gh (pr comment)"
    else
        # Fallback to gh api with explicit body content
        gh api repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments \
          -f body="$(cat "$COMMENT_FILE")"
        log_success "PR comment posted successfully via gh api"
    fi
else
    log_info "gh not found, using curl to post PR comment"
    # Fallback without requiring jq: safely JSON-encode body using Python
    JSON_BODY=$(uv run python scripts/utils/json_encode_body.py "$COMMENT_FILE")
    curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" \
         -H "Accept: application/vnd.github+json" \
         -H "X-GitHub-Api-Version: 2022-11-28" \
         -X POST \
         -d "$JSON_BODY" \
         "https://api.github.com/repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments"
    log_success "PR comment posted successfully via curl"
fi