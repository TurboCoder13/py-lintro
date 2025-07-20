#!/bin/bash

# CI Post PR Comment Script
# Handles posting comments to PRs using GitHub API

set -e

# Source shared utilities
source "$(dirname "$0")/utils.sh"

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