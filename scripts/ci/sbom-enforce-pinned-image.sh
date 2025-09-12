#!/usr/bin/env bash
set -euo pipefail

# sbom-enforce-pinned-image.sh
# Ensure BOMCTL_IMAGE is set and digest-pinned (@sha256:...)

ref="${BOMCTL_IMAGE:-}"
if [[ -z "${ref}" ]]; then
  echo "BOMCTL_IMAGE is not set. Set a digest-pinned image like 'bomctl/bomctl@sha256:...'" >&2
  exit 1
fi
if [[ "${ref}" != *@sha256:* ]]; then
  echo "BOMCTL_IMAGE must be digest-pinned (contains '@sha256:'). Got: ${ref}" >&2
  exit 1
fi
echo "BOMCTL_IMAGE is digest-pinned: ${ref}" >&2


