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

# Create the GitHub script content
cat > post-comment.js << 'EOF'
const fs = require('fs');
const commentFile = process.argv[2] || 'pr-comment.txt';

try {
    const comment = fs.readFileSync(commentFile, 'utf8');
    
    github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: comment
    });
    
    console.log('✅ PR comment posted successfully');
} catch (error) {
    console.error('❌ Failed to post PR comment:', error.message);
    process.exit(1);
}
EOF

# Execute the GitHub script
node post-comment.js "$COMMENT_FILE"

log_success "PR comment posted successfully" 