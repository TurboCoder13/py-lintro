#!/usr/bin/env bash
set -euo pipefail

# sbom-verify-container.sh
# Verify a digest-pinned container image using cosign keyless.

REF="${BOMCTL_IMAGE:-}"
if [[ -z "${REF}" || "${REF}" != *@sha256:* ]]; then
  echo "BOMCTL_IMAGE not set to a digest-pinned reference; skipping verify"
  exit 0
fi

if ! command -v cosign >/dev/null 2>&1; then
  echo "cosign not installed; skipping verify"
  exit 0
fi

export COSIGN_EXPERIMENTAL=1
set +e
cosign verify \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-identity-regexp 'https://github\.com/bomctl/bomctl/\.github/.+' \
  "${REF}"
rc=$?
set -e
if [ $rc -ne 0 ]; then
  echo "cosign verify failed or signature not found" >&2
  exit 1
fi
echo "cosign verify OK for ${REF}"


