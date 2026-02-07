#!/usr/bin/env bash
set -euo pipefail

# Pull the pre-built lintro Docker image from GHCR and tag it for local use.
# Logs the resolved digest for traceability.

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
	echo "Usage: $0 [--help]"
	echo ""
	echo "Pull Lintro Docker Image"
	echo "Pulls the pre-built lintro Docker image from GHCR and tags it locally."
	echo ""
	echo "Features:"
	echo "  - Pulls ghcr.io/lgtm-hq/py-lintro:latest from GHCR"
	echo "  - Tags as py-lintro:latest for local use"
	echo "  - Logs the resolved image digest for traceability"
	echo ""
	echo "This script is designed to be run in GitHub Actions CI environment."
	exit 0
fi

IMAGE="ghcr.io/lgtm-hq/py-lintro:latest"

docker pull "$IMAGE"
docker tag "$IMAGE" py-lintro:latest

DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' "$IMAGE")
if [ -z "$DIGEST" ]; then
	echo "::error::Failed to resolve image digest for $IMAGE" >&2
	exit 1
fi
echo "::notice::Resolved digest: $DIGEST"
