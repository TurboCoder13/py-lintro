#!/usr/bin/env bash
set -euo pipefail

# mirror-bomctl-to-ghcr.sh
# Mirror bomctl from Docker Hub to GHCR and update BOMCTL_IMAGE repo variable.
#
# Behavior:
# - Pulls source image (default: bomctl/bomctl:latest) with a specific platform
# - Tags and pushes to GHCR under the current repository owner namespace
# - Extracts the pushed digest and updates the BOMCTL_IMAGE variable via gh CLI
#
# Env (optional):
# - SRC_IMAGE               Source image (default: bomctl/bomctl:latest)
# - DOCKER_PLATFORM         Platform to pull (default: linux/amd64)
# - GHCR_REPO_NAME          Target image name in GHCR (default: bomctl)
# - GHCR_OWNER              Target owner/namespace (default: repo owner)
# - DOCKERHUB_USERNAME      If set with DOCKERHUB_TOKEN, logs into Docker Hub
# - DOCKERHUB_TOKEN         Docker Hub token/password
# - GHCR_USERNAME           If set with GHCR_TOKEN, logs into GHCR (usually done in workflow)
# - GHCR_TOKEN              GHCR token (prefer GITHUB_TOKEN via workflow)
# - GH_TOKEN                GitHub token for gh CLI (defaults from GITHUB_TOKEN)

show_help() {
  printf '%s\n' \
    "mirror-bomctl-to-ghcr.sh" \
    "" \
    "Mirror the bomctl container from Docker Hub to GHCR and update the" \
    "repository variable BOMCTL_IMAGE with the pushed digest." \
    "" \
    "Environment variables:" \
    "  SRC_IMAGE            Source image (default: bomctl/bomctl:latest)" \
    "  DOCKER_PLATFORM      Platform for pull (default: linux/amd64)" \
    "  GHCR_REPO_NAME       Target image name in GHCR (default: bomctl)" \
    "  GHCR_OWNER           Target owner/namespace (default: repo owner)" \
    "  GHCR_USERNAME        Username for GHCR login (optional)" \
    "  GHCR_TOKEN           Token/password for GHCR login (optional)" \
    "  DOCKERHUB_USERNAME   Username for Docker Hub login (optional)" \
    "  DOCKERHUB_TOKEN      Token/password for Docker Hub login (optional)" \
    "  GH_TOKEN/GITHUB_TOKEN Token for gh CLI to update repo variables" \
    "" \
    "Usage:" \
    "  scripts/ci/mirror-bomctl-to-ghcr.sh" \
    "" \
    "Notes:" \
    "  - In CI, prefer using the built-in GITHUB_TOKEN to authenticate gh CLI." \
    "  - If GHCR_USERNAME/GHCR_TOKEN are not provided, ensure the workflow logs in."
}

# Handle --help early to avoid requiring docker/gh during help display
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

log() { echo "[mirror] $*"; }
err() { echo "[mirror][err] $*" >&2; }

# Derive owner from GITHUB_REPOSITORY if not provided
derive_owner() {
  if [[ -n "${GHCR_OWNER:-}" ]]; then
    echo "$GHCR_OWNER"
    return 0
  fi
  if [[ -n "${GITHUB_REPOSITORY:-}" ]]; then
    echo "${GITHUB_REPOSITORY%%/*}"
    return 0
  fi
  if command -v git >/dev/null 2>&1 && git remote get-url origin >/dev/null 2>&1; then
    local url
    url=$(git remote get-url origin)
    case "$url" in
      *github.com/*)
        url="${url##*:}"; url="${url##*/github.com/}"; url="${url%.git}"
        echo "${url%%/*}"
        return 0
        ;;
    esac
  fi
  err "Unable to determine GHCR owner. Set GHCR_OWNER."
  return 1
}

main() {
  local src_image="${SRC_IMAGE:-bomctl/bomctl:latest}"
  local platform="${DOCKER_PLATFORM:-linux/amd64}"
  local owner
  owner=$(derive_owner)
  local repo_name="${GHCR_REPO_NAME:-bomctl}"
  local target_image="ghcr.io/${owner}/${repo_name}:latest"

  # Optional: Docker Hub login
  if [[ -n "${DOCKERHUB_USERNAME:-}" && -n "${DOCKERHUB_TOKEN:-}" ]]; then
    log "Logging into Docker Hub..."
    if ! printf '%s' "$DOCKERHUB_TOKEN" | docker login docker.io -u "$DOCKERHUB_USERNAME" --password-stdin; then
      err "Docker Hub login failed (continuing, may hit rate limits)"
    fi
  fi

  # Optional: GHCR login (usually done in workflow)
  if [[ -n "${GHCR_USERNAME:-}" && -n "${GHCR_TOKEN:-}" ]]; then
    log "Logging into GHCR..."
    printf '%s' "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin
  fi

  log "Pulling source image: ${src_image} (platform=${platform})"
  docker pull --platform "${platform}" "${src_image}"

  log "Tagging for GHCR: ${target_image}"
  docker tag "${src_image}" "${target_image}"

  log "Pushing to GHCR: ${target_image}"
  local push_out
  # Capture push output to extract digest
  if ! push_out=$(docker push "${target_image}" 2>&1); then
    echo "${push_out}" >&2
    err "Push failed"
    exit 1
  fi
  echo "${push_out}"

  # Extract digest from push output, fallback to docker inspect
  local digest
  digest=$(echo "${push_out}" | awk '/digest: sha256:/ {for(i=1;i<=NF;i++){if($i ~ /sha256:.*/){print $i}}}' | sed 's/,//g' | tail -n1)
  if [[ -z "${digest}" ]]; then
    log "Falling back to docker inspect for digest..."
    local repod
    repod=$(docker inspect --format='{{json .RepoDigests}}' "${target_image}" | tr -d '[]"' | tr ' ' '\n' | grep -F 'ghcr.io/' | tail -n1 | cut -d'@' -f2 || true)
    digest="${repod:-}"
  fi
  if [[ -z "${digest}" ]]; then
    err "Unable to determine pushed digest"
    exit 1
  fi

  local full_ref="ghcr.io/${owner}/${repo_name}@${digest}"
  log "New GHCR digest: ${full_ref}"

  # Update repo variable via gh CLI
  export GH_TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
  if ! command -v gh >/dev/null 2>&1; then
    err "gh CLI is required to update repository variables"
    exit 1
  fi
  if [[ -z "${GH_TOKEN:-}" ]]; then
    err "GH_TOKEN/GITHUB_TOKEN is required for gh CLI"
    exit 1
  fi

  log "Updating repository variable BOMCTL_IMAGE..."
  gh variable set BOMCTL_IMAGE --body "${full_ref}"
  log "BOMCTL_IMAGE updated to ${full_ref}"
}

main "$@"


