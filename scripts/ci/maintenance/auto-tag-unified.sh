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

# Determine Python command to use (uv run python if available, else python3/python)
get_python_cmd() {
    if command -v uv >/dev/null 2>&1; then
        echo "uv run python"
    elif command -v python3 >/dev/null 2>&1; then
        echo "python3"
    else
        echo "python"
    fi
}

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

# Check for help flag before sourcing utils (to avoid path issues)
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    show_help
    exit 0
fi

# Source utilities
source "$(dirname "${BASH_SOURCE[0]}")/../../utils/utils.sh"

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
        return 0
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
    local script_dir
    script_dir="$(dirname "${BASH_SOURCE[0]}")"
    
    # Get the previous commit SHA
    local prev_commit
    prev_commit=$(git rev-parse HEAD~1 2>/dev/null || true)
    
    if [[ -z "$prev_commit" ]]; then
        echo "version=" >> "${GITHUB_OUTPUT:-/dev/stdout}"
        echo "No previous commit found"
        return
    fi
    
    # Create temporary file for previous commit's pyproject.toml
    local temp_file
    temp_file=$(mktemp)
    trap "rm -f '$temp_file'" EXIT
    
    # Extract pyproject.toml from previous commit
    if ! git show "$prev_commit:pyproject.toml" > "$temp_file" 2>/dev/null; then
        echo "version=" >> "${GITHUB_OUTPUT:-/dev/stdout}"
        echo "Could not access pyproject.toml from previous commit"
        return
    fi
    
    # Use robust Python-based version extraction on the temporary file
    local extract_output
    local python_cmd
    python_cmd=$(get_python_cmd)
    extract_output=$($python_cmd "${script_dir}/../utils/extract-version.py" --file "$temp_file" 2>&1)
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]] && [[ -n "$extract_output" ]]; then
        # Extract version value from "version=X.Y.Z" output
        previous_version="${extract_output#version=}"
        
        if [[ -n "$previous_version" ]]; then
            echo "version=$previous_version" >> "${GITHUB_OUTPUT:-/dev/stdout}"
            echo "Previous version: $previous_version"
        else
            echo "version=" >> "${GITHUB_OUTPUT:-/dev/stdout}"
            echo "Could not extract version from previous commit's pyproject.toml"
        fi
    else
        echo "version=" >> "${GITHUB_OUTPUT:-/dev/stdout}"
        echo "Could not extract version from previous commit's pyproject.toml"
    fi
}

read_version_from_pyproject() {
    local version
    local script_dir
    script_dir="$(dirname "${BASH_SOURCE[0]}")"
    
    if [[ ! -f "pyproject.toml" ]]; then
        echo "Error: pyproject.toml not found" >&2
        exit 1
    fi
    
    # Use robust Python-based version extraction
    local extract_output
    local python_cmd
    python_cmd=$(get_python_cmd)
    extract_output=$($python_cmd "${script_dir}/../utils/extract-version.py" 2>&1)
    local exit_code=$?
    
    if [[ $exit_code -ne 0 ]]; then
        echo "Error: Failed to extract version from pyproject.toml: $extract_output" >&2
        exit 1
    fi
    
    # Extract version value from "version=X.Y.Z" output
    version="${extract_output#version=}"
    
    if [[ -z "$version" ]]; then
        echo "Error: Could not extract version from pyproject.toml" >&2
        exit 1
    fi
    
    # Don't add 'v' prefix here - let the calling workflow handle prefixing
    # This prevents double-prefixing when workflows add "v" to the output
    
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
