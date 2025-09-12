#!/usr/bin/env bash
set -euo pipefail

# sbom-install-binary-gh.sh
# Install bomctl via GitHub Releases using gh CLI (pinned version pattern).
# Uses only GitHub endpoints (api.github.com, release-assets), avoiding GHCR/Docker Hub.

VERSION="${BOMCTL_VERSION:-v0.4.3}"

# Ensure gh is available
if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found on runner" >&2
  exit 1
fi

# Map token for gh if provided
if [[ -z "${GH_TOKEN:-}" && -n "${GITHUB_TOKEN:-}" ]]; then
  export GH_TOKEN="${GITHUB_TOKEN}"
fi

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

echo "[bomctl] Downloading ${VERSION} via gh release (Linux x86_64)..." >&2
gh release download "${VERSION}" -R bomctl/bomctl \
  -p 'bomctl_*_Linux_x86_64.tar.gz' -O "${tmpdir}/bomctl.tgz"

tar -C "${tmpdir}" -xzf "${tmpdir}/bomctl.tgz" bomctl
install -m 0755 "${tmpdir}/bomctl" /usr/local/bin/bomctl
echo "[bomctl] Installed to /usr/local/bin/bomctl" >&2


