#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Resolve the tools image tag for reusable workflow callers.
# Outputs: tag (via GITHUB_OUTPUT)

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Resolve the tools image tag for reusable workflow callers.

Usage:
  scripts/ci/tools-image-resolve-tag.sh

Environment Variables (required):
  GITHUB_OUTPUT  Path to GitHub output file

Environment Variables (optional):
  BUILD_TAG      Tag from build-tools-image job (if build ran)
  BUILD_RESULT   Result of build-tools-image job (success, failure, skipped)
  DEFAULT_IMAGE  Default image to use as fallback (default: ghcr.io/turbocoder13/lintro-tools:latest)

Outputs (to GITHUB_OUTPUT):
  tag            The resolved tools image tag

Example:
  GITHUB_OUTPUT=/tmp/output BUILD_RESULT=success BUILD_TAG=ghcr.io/turbocoder13/lintro-tools:pr-123 \
    ./scripts/ci/tools-image-resolve-tag.sh
EOF
	exit 0
fi

: "${GITHUB_OUTPUT:?GITHUB_OUTPUT must be set}"

BUILD_TAG="${BUILD_TAG:-}"
BUILD_RESULT="${BUILD_RESULT:-}"
DEFAULT_IMAGE="${DEFAULT_IMAGE:-ghcr.io/turbocoder13/lintro-tools:latest}"

# If build ran and succeeded, use its tag
if [[ "$BUILD_RESULT" == "success" && -n "$BUILD_TAG" ]]; then
	echo "tag=$BUILD_TAG" >>"$GITHUB_OUTPUT"
	echo "Using built image tag: $BUILD_TAG"
else
	# Fall back to default (:latest)
	echo "tag=$DEFAULT_IMAGE" >>"$GITHUB_OUTPUT"
	echo "Using fallback image tag: $DEFAULT_IMAGE"
fi
