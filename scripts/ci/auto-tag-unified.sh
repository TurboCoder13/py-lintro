#!/usr/bin/env bash
set -euo pipefail

# auto-tag-unified.sh
# Unified auto-tagging functionality consolidating 5 separate scripts
# 
# Usage:
#   scripts/ci/auto-tag-unified.sh [--help|-h] [COMMAND]
#
# Commands:
#   check-exists [TAG]     - Check if tag exists
#   configure-auth         - Configure git authentication
#   create-push [TAG]      - Create and push tag
#   detect-previous        - Detect previous version
#   read-version           - Read version from pyproject.toml
#
# Environment Variables:
#   TAG                    - Tag to work with
#   GITHUB_OUTPUT         - GitHub Actions output file
#   GITHUB_TOKEN          - GitHub token for authentication

# Source utilities
source "$(dirname "${BASH_SOURCE[0]}")/../utils/utils.sh"

show_help() {
    cat <<'EOF'
Unified auto-tagging script for GitHub Actions workflows.

Commands:
  check-exists [TAG]     Check if a git tag exists
  configure-auth         Configure git authentication for tagging
  create-push [TAG]      Create and push a new tag
  detect-previous        Detect the previous version tag
  read-version           Read version from pyproject.toml

Examples:
  auto-tag-unified.sh check-exists v1.2.3
  auto-tag-unified.sh configure-auth
  auto-tag-unified.sh create-push v1.2.3
  auto-tag-unified.sh detect-previous
  auto-tag-unified.sh read-version
EOF
}

check_tag_exists() {
    local tag="${1:-${TAG:-}}"
    
    if [[ -z "$tag" ]]; then
        echo "Error: TAG is required" >&2
        exit 1
    fi
    
    if git rev-parse --verify "refs/tags/$tag" >/dev/null 2>&1; then
        echo "exists=true" >> "${GITHUB_OUTPUT:-/dev/stdout}"
        echo "Tag $tag exists"
        return 0
    else
        echo "exists=false" >> "${GITHUB_OUTPUT:-/dev/stdout}"
        echo "Tag $tag does not exist"
        return 1
    fi
}

configure_auth() {
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
        echo "Error: GITHUB_TOKEN is required" >&2
        exit 1
    fi
    
    # Configure git for GitHub Actions
    git config --global user.name "github-actions[bot]"
    git config --global user.email "github-actions[bot]@users.noreply.github.com"
    
    # Configure authentication
    git config --global url."https://x-access-token:${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/"
    
    echo "Git authentication configured"
}

create_and_push_tag() {
    local tag="${1:-${TAG:-}}"
    
    if [[ -z "$tag" ]]; then
        echo "Error: TAG is required" >&2
        exit 1
    fi
    
    # Verify tag doesn't already exist
    if git rev-parse --verify "refs/tags/$tag" >/dev/null 2>&1; then
        echo "Error: Tag $tag already exists" >&2
        exit 1
    fi
    
    # Create annotated tag
    git tag -a "$tag" -m "Release $tag"
    
    # Push tag
    git push origin "$tag"
    
    echo "tag=$tag" >> "${GITHUB_OUTPUT:-/dev/stdout}"
    echo "Created and pushed tag: $tag"
}

detect_previous_version() {
    # Read version from the previous commit's pyproject.toml (original behavior)
    local previous_version
    
    # Get the previous commit SHA
    local prev_commit
    prev_commit=$(git rev-parse HEAD~1 2>/dev/null || true)
    
    if [[ -z "$prev_commit" ]]; then
        echo "version=" >> "${GITHUB_OUTPUT:-/dev/stdout}"
        echo "No previous commit found"
        return
    fi
    
    # Extract version from previous commit's pyproject.toml
    previous_version=$(git show "$prev_commit:pyproject.toml" 2>/dev/null | grep '^version = ' | sed 's/version = "\(.*\)"/\1/' || true)
    
    if [[ -n "$previous_version" ]]; then
        echo "version=$previous_version" >> "${GITHUB_OUTPUT:-/dev/stdout}"
        echo "Previous version: $previous_version"
    else
        echo "version=" >> "${GITHUB_OUTPUT:-/dev/stdout}"
        echo "Could not extract version from previous commit's pyproject.toml"
    fi
}

read_version_from_pyproject() {
    local version
    
    if [[ ! -f "pyproject.toml" ]]; then
        echo "Error: pyproject.toml not found" >&2
        exit 1
    fi
    
    # Extract version from pyproject.toml
    version=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
    
    if [[ -z "$version" ]]; then
        echo "Error: Could not extract version from pyproject.toml" >&2
        exit 1
    fi
    
    # Add v prefix if not present
    if [[ ! "$version" =~ ^v ]]; then
        version="v$version"
    fi
    
    echo "version=$version" >> "${GITHUB_OUTPUT:-/dev/stdout}"
    echo "Version: $version"
}

main() {
    local command="${1:-}"
    
    case "$command" in
        "--help"|"-h"|"help")
            show_help
            exit 0
            ;;
        "check-exists")
            shift
            check_tag_exists "$@"
            ;;
        "configure-auth")
            configure_auth
            ;;
        "create-push")
            shift
            create_and_push_tag "$@"
            ;;
        "detect-previous")
            detect_previous_version
            ;;
        "read-version")
            read_version_from_pyproject
            ;;
        "")
            echo "Error: Command is required" >&2
            show_help
            exit 1
            ;;
        *)
            echo "Error: Unknown command: $command" >&2
            show_help
            exit 1
            ;;
    esac
}

main "$@"
