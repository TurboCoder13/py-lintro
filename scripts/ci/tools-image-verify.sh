#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Verify that all required tools are installed in the tools image.

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Verify that all required tools are installed in the tools image.

Usage:
  scripts/ci/tools-image-verify.sh

Environment Variables (optional):
  IMAGE   Docker image to verify (default: lintro-tools:test)

The script runs tool version checks inside the specified Docker image
to ensure all linting/formatting tools are properly installed.

Example:
  IMAGE=ghcr.io/lgtm-hq/lintro-tools:latest ./scripts/ci/tools-image-verify.sh
EOF
	exit 0
fi

IMAGE="${IMAGE:-lintro-tools:test}"

echo "Verifying installed tools in ${IMAGE}..."

# Run manifest-driven verification inside the container
docker run --rm "$IMAGE" python3 /app/scripts/ci/verify-manifest-tools.py \
	--manifest /app/lintro/tools/manifest.json \
	--tiers tools

echo "All tools verified successfully!"
