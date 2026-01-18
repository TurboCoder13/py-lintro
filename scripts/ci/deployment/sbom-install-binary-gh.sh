#!/usr/bin/env bash
set -euo pipefail

# sbom-install-binary-gh.sh
# Install bomctl via GitHub Releases using gh CLI (pinned version pattern).
# Uses only GitHub endpoints (api.github.com, release-assets), avoiding GHCR/Docker Hub.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'USAGE'
Usage: scripts/ci/sbom-install-binary-gh.sh [--help|-h]

Install bomctl via GitHub Releases using gh CLI (pinned version pattern).

Environment:
  BOMCTL_VERSION  Optional. Release tag (default: v0.4.3)
  GITHUB_TOKEN    Optional. GitHub token for API access
USAGE
	exit 0
fi

VERSION="${BOMCTL_VERSION:-v0.4.3}"

# Ensure gh is available
if ! command -v gh >/dev/null 2>&1; then
	echo "gh CLI not found on runner" >&2
	exit 1
fi

# Set GH_TOKEN for gh CLI from GITHUB_TOKEN if available
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
	export GH_TOKEN="${GITHUB_TOKEN}"
fi

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

echo "[bomctl] Resolving asset for ${VERSION} via gh API..." >&2
asset=$(gh release view "${VERSION}" -R bomctl/bomctl --json assets --jq \
	'.assets[].name | select(test("(?i)linux") and (test("x86_64|amd64")) and (endswith(".tar.gz")))' | head -n1)

if [[ -z "${asset}" ]]; then
	echo "[bomctl] No matching Linux amd64 .tar.gz asset found in ${VERSION}" >&2
	exit 1
fi

echo "[bomctl] Downloading asset: ${asset}" >&2
gh release download "${VERSION}" -R bomctl/bomctl -p "${asset}" -O "${tmpdir}/bomctl.tgz"

tar -C "${tmpdir}" -xzf "${tmpdir}/bomctl.tgz" bomctl
install -m 0755 "${tmpdir}/bomctl" /usr/local/bin/bomctl
echo "[bomctl] Installed to /usr/local/bin/bomctl" >&2
