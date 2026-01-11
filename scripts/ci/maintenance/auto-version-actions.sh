#!/usr/bin/env bash
set -euo pipefail

# auto-version-actions.sh
# Automatically version internal actions/workflows with semantic version tags.
# Creates patch version tags (actions-v1.0.1, actions-v1.0.2, etc.) when actions change.

show_help() {
  cat <<'EOF'
Usage: scripts/ci/auto-version-actions.sh [OPTIONS]

Automatically creates semantic version tags for internal GitHub Actions.

Options:
  --help, -h          Show this help message
  --dry-run           Show what would be done without making changes
  --push              Push the created tag to remote (default: true)
  --no-push           Don't push the tag to remote

Environment Variables:
  GITHUB_OUTPUT       Path to GitHub Actions output file (for CI)
  DRY_RUN             Set to '1' for dry-run mode

Examples:
  # Normal usage in CI
  scripts/ci/auto-version-actions.sh

  # Dry run to see what would happen
  scripts/ci/auto-version-actions.sh --dry-run

  # Create tag but don't push
  scripts/ci/auto-version-actions.sh --no-push

EOF
}

# Parse arguments
DRY_RUN="${DRY_RUN:-}"
SHOULD_PUSH="true"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      show_help
      exit 0
      ;;
    --dry-run)
      DRY_RUN="1"
      shift
      ;;
    --push)
      SHOULD_PUSH="true"
      shift
      ;;
    --no-push)
      SHOULD_PUSH="false"
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      show_help
      exit 1
      ;;
  esac
done

# Helper functions
log_info() {
  echo "[INFO] $*" >&2
}

log_error() {
  echo "[ERROR] $*" >&2
}

set_github_output() {
  local key="$1"
  local value="$2"
  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    echo "${key}=${value}" >> "$GITHUB_OUTPUT"
  fi
}

# Get latest actions-v1.x.x tag
get_latest_tag() {
  local latest
  latest=$(git tag -l 'actions-v1.*.*' | sort -V | tail -n1)
  
  if [[ -z "$latest" ]]; then
    # No actions-v1.x.x tags exist yet, return sentinel value
    log_info "No existing actions-v1.x.x tags found, will create actions-v1.0.0"
    echo "NONE"
  else
    log_info "Latest tag: $latest"
    echo "$latest"
  fi
}

# Increment patch version
increment_version() {
  local latest="$1"
  
  # If no tags exist (sentinel value), return v1.0.0 directly
  if [[ "$latest" == "NONE" ]]; then
    log_info "Next tag: actions-v1.0.0"
    echo "actions-v1.0.0"
    return 0
  fi
  
  # Remove 'actions-v' prefix, split into parts, increment patch
  local version="${latest#actions-v}"
  local major minor patch
  major=$(echo "$version" | cut -d. -f1)
  minor=$(echo "$version" | cut -d. -f2)
  patch=$(echo "$version" | cut -d. -f3)
  
  # Increment patch version
  local next_patch=$((patch + 1))
  local next_tag="actions-v${major}.${minor}.${next_patch}"
  
  log_info "Next tag: $next_tag"
  echo "$next_tag"
}

# Check if tag exists
tag_exists() {
  local tag="$1"
  if git rev-parse "$tag" >/dev/null 2>&1; then
    return 0
  else
    return 1
  fi
}

# Create and push tag
create_and_push_tag() {
  local tag="$1"
  local message="chore: auto-version internal actions to $tag"

  if [[ -n "$DRY_RUN" ]]; then
    log_info "[DRY-RUN] Would create tag: $tag"
    log_info "[DRY-RUN] Would push tag to origin"
    return 0
  fi

  # Configure git (for CI environments)
  git config user.name "github-actions[bot]"
  git config user.email "github-actions[bot]@users.noreply.github.com"

  # Create annotated tag
  git tag -a "$tag" -m "$message"
  log_info "✅ Created tag: $tag"

  # Push tag if requested
  if [[ "$SHOULD_PUSH" == "true" ]]; then
    git push origin "$tag"
    log_info "✅ Pushed tag: $tag"
  else
    log_info "⏸️  Skipped pushing tag (--no-push specified)"
  fi
}

# Main logic
main() {
  # Get latest tag
  local latest_tag
  latest_tag=$(get_latest_tag)
  set_github_output "latest_tag" "$latest_tag"
  
  # Increment version
  local next_tag
  next_tag=$(increment_version "$latest_tag")
  set_github_output "next_tag" "$next_tag"
  
  # Check if tag exists
  if tag_exists "$next_tag"; then
    log_info "Tag $next_tag already exists, skipping"
    set_github_output "tag_exists" "true"
    set_github_output "tag_created" "false"
    return 0
  fi
  
  set_github_output "tag_exists" "false"
  
  # Create and push tag
  create_and_push_tag "$next_tag"
  set_github_output "tag_created" "true"

  log_info "Internal actions automatically versioned to $next_tag"
  log_info "Update workflow references to use @$next_tag"
}

# Run main
main "$@"

