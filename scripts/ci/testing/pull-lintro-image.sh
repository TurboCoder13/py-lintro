#!/usr/bin/env bash
set -euo pipefail

# Pull the pre-built lintro Docker image from GHCR and tag it for local use.
# Logs the resolved digest for traceability.

IMAGE="ghcr.io/lgtm-hq/py-lintro:latest"

docker pull "$IMAGE"
docker tag "$IMAGE" py-lintro:latest

DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' "$IMAGE")
if [ -z "$DIGEST" ]; then
	echo "::error::Failed to resolve image digest for $IMAGE" >&2
	exit 1
fi
echo "::notice::Resolved digest: $DIGEST"
