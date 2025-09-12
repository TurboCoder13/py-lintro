#!/usr/bin/env bash
set -euo pipefail

# sbom-bomctl-run.sh
# Run basic bomctl operations via container (GHCR) in CI.
# - Prints bomctl help (sanity)
# - Fetches dependency graph SBOM for current repo

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'USAGE'
Usage: scripts/ci/sbom-bomctl-run.sh

Environment:
  BOMCTL_IMAGE      Container image ref (default: ghcr.io/bomctl/bomctl:0.4.3)
  GITHUB_REPOSITORY owner/repo (GitHub Actions provides this)
  GITHUB_TOKEN      Token for GitHub API (passed to container for fetch)
USAGE
  exit 0
fi

IMAGE_REF="${BOMCTL_IMAGE:-ghcr.io/bomctl/bomctl:0.4.3}"

echo "[bomctl] Using image: ${IMAGE_REF}" >&2

# Best-effort pull (allows GHCR auth via prior workflow login)
if ! docker pull "${IMAGE_REF}" >/dev/null 2>&1; then
  echo "[bomctl] Warning: docker pull failed; continuing (image may still be cached)" >&2
fi

echo "[bomctl] Printing help (sanity)..." >&2
docker run --rm "${IMAGE_REF}" --help | sed -n '1,40p' || true

REPO_URL="https://github.com/${GITHUB_REPOSITORY:-}"
if [[ -z "${GITHUB_REPOSITORY:-}" ]]; then
  echo "[bomctl] GITHUB_REPOSITORY is not set; cannot infer repo URL" >&2
  exit 2
fi

echo "[bomctl] Fetching SBOM for ${REPO_URL}" >&2
docker run --rm \
  -e GITHUB_TOKEN \
  -v "$PWD:/work" -w /work \
  "${IMAGE_REF}" \
  fetch "${REPO_URL}"

echo "[bomctl] Done"


