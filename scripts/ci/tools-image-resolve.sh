#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# For license details, see the repository root LICENSE file.
#
# Resolve the tools image tag based on context.
# Used by resolve-tools-image action.
#
# Required environment variables:
#   TOOLS_CHANGED       - "true" or "false"
#   GITHUB_EVENT_NAME   - "push" or "pull_request"
#   IMAGE_NAME          - Base image name (e.g., ghcr.io/lgtm-hq/lintro-tools)
#   STABLE_IMAGE        - Full stable image reference with digest
#   GITHUB_OUTPUT       - Path to GitHub outputs file
# Optional:
#   PR_NUMBER           - PR number (required if pull_request + tools changed)

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Resolve the tools image tag based on context.

Usage:
  scripts/ci/tools-image-resolve.sh

Environment Variables (required):
  TOOLS_CHANGED       "true" or "false" - whether tool files changed
  GITHUB_EVENT_NAME   GitHub event name (push or pull_request)
  IMAGE_NAME          Base image name (e.g., ghcr.io/lgtm-hq/lintro-tools)
  STABLE_IMAGE        Full stable image reference with digest
  GITHUB_OUTPUT       Path to GitHub output file

Environment Variables (optional):
  PR_NUMBER           PR number (required if pull_request + tools changed)

Outputs (to GITHUB_OUTPUT):
  image               Full image reference to use

Logic:
  - PR with tool changes:  IMAGE_NAME:pr-PR_NUMBER
  - Push with tool changes: IMAGE_NAME:latest
  - No tool changes:        STABLE_IMAGE (pinned digest)

Example:
  TOOLS_CHANGED=false GITHUB_EVENT_NAME=push IMAGE_NAME=ghcr.io/org/tools \
    STABLE_IMAGE=ghcr.io/org/tools:latest@sha256:abc GITHUB_OUTPUT=/tmp/out \
    ./scripts/ci/tools-image-resolve.sh
EOF
	exit 0
fi

: "${TOOLS_CHANGED:?TOOLS_CHANGED is required}"
: "${GITHUB_EVENT_NAME:?GITHUB_EVENT_NAME is required}"
: "${IMAGE_NAME:?IMAGE_NAME is required}"
: "${STABLE_IMAGE:?STABLE_IMAGE is required}"
: "${GITHUB_OUTPUT:?GITHUB_OUTPUT is required}"

if [[ "$TOOLS_CHANGED" == "true" ]] &&
	[[ "$GITHUB_EVENT_NAME" == "pull_request" ]]; then
	# For PRs with tool changes, PR_NUMBER is required
	if [[ -z "${PR_NUMBER:-}" ]]; then
		echo "::error::PR_NUMBER is required when TOOLS_CHANGED=true and event is pull_request"
		echo "  IMAGE_NAME=${IMAGE_NAME}"
		echo "  PR_NUMBER=${PR_NUMBER:-<unset>}"
		exit 1
	fi
	# Use the freshly built pr-N image
	IMAGE="${IMAGE_NAME}:pr-${PR_NUMBER}"
	echo "Using fresh tools image for PR: ${IMAGE}"
elif [[ "$GITHUB_EVENT_NAME" == "push" ]]; then
	# For ALL push events on main, use :latest tag (not pinned digest)
	# This ensures we always use the current tools image, avoiding race conditions
	# where the pinned digest in STABLE_IMAGE hasn't been updated yet.
	# The :latest tag is authoritative for main branch builds.
	IMAGE="${IMAGE_NAME}:latest"
	if [[ "$TOOLS_CHANGED" == "true" ]]; then
		echo "Using latest tools image (tool files changed on push): ${IMAGE}"
	else
		echo "Using latest tools image (main branch always uses latest): ${IMAGE}"
	fi
else
	# For PRs without tool changes, use stable image (pinned digest)
	# This ensures PR builds are reproducible and don't break if :latest drifts
	IMAGE="${STABLE_IMAGE}"
	echo "Using stable tools image: ${IMAGE}"
fi

echo "image=${IMAGE}" >>"$GITHUB_OUTPUT"
