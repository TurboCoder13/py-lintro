#!/usr/bin/env bash
set -euo pipefail

# sbom-install-binary.sh
# Install bomctl from a pinned release tarball URL with SHA256 verification.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'USAGE'
Usage: scripts/ci/sbom-install-binary.sh [--help|-h]

Install bomctl from a pinned release tarball URL with SHA256 verification.

Environment:
  BOMCTL_URL     Required. HTTPS URL to a release tarball containing 'bomctl'.
  BOMCTL_SHA256  Required. Expected SHA256 digest of the tarball.
USAGE
  exit 0
fi

if [[ -z "${BOMCTL_URL:-}" || -z "${BOMCTL_SHA256:-}" ]]; then
  echo "BOMCTL_URL or BOMCTL_SHA256 not set." >&2
  exit 1
fi

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

echo "[bomctl] Downloading binary from ${BOMCTL_URL}" >&2
curl -fsSL "$BOMCTL_URL" -o "$tmpdir/bomctl.tar.gz"
echo "${BOMCTL_SHA256}  $tmpdir/bomctl.tar.gz" | sha256sum -c -
tar -C "$tmpdir" -xzf "$tmpdir/bomctl.tar.gz" bomctl
install -m 0755 "$tmpdir/bomctl" /usr/local/bin/bomctl
echo "[bomctl] Installed to /usr/local/bin/bomctl" >&2


