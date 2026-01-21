#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Generate Docker image tags for the tools image build.
# Outputs: tags, push_latest, pr_tag (via GITHUB_OUTPUT)

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Generate Docker image tags for the tools image build.

Usage:
  scripts/ci/tools-image-tags.sh

Environment Variables (required):
  GITHUB_OUTPUT  Path to GitHub output file
  EVENT_NAME     GitHub event name (push, pull_request, schedule, workflow_dispatch)
  GIT_REF        Git ref (e.g., refs/heads/main)

Environment Variables (optional):
  IMAGE_BASE     Base image name (default: ghcr.io/turbocoder13/lintro-tools)
  FORCE_LATEST   Force :latest tag on workflow_dispatch (default: false)
  PR_NUMBER      PR number for PR-specific tags

Outputs (to GITHUB_OUTPUT):
  tags           Comma-separated list of image tags
  push_latest    Whether :latest tag should be pushed
  pr_tag         PR-specific tag if applicable

Example:
  GITHUB_OUTPUT=/tmp/output EVENT_NAME=push GIT_REF=refs/heads/main \
    ./scripts/ci/tools-image-tags.sh
EOF
	exit 0
fi

: "${GITHUB_OUTPUT:?GITHUB_OUTPUT must be set}"
: "${EVENT_NAME:?EVENT_NAME must be set}"
: "${GIT_REF:?GIT_REF must be set}"

IMAGE_BASE="${IMAGE_BASE:-ghcr.io/turbocoder13/lintro-tools}"
FORCE_LATEST="${FORCE_LATEST:-false}"
PR_NUMBER="${PR_NUMBER:-}"

SHORT_SHA=$(git rev-parse --short HEAD)
IS_PR=$([[ "$EVENT_NAME" == "pull_request" ]] && echo true || echo false)

# Start with SHA tag (always included)
TAGS="${IMAGE_BASE}:sha-${SHORT_SHA}"

# Add date tag only for non-PR events
if [[ "$IS_PR" != "true" ]]; then
	DATE_TAG=$(date -u +%Y-%m-%d)
	TAGS="${TAGS},${IMAGE_BASE}:${DATE_TAG}"
fi

# Add :latest for main branch pushes, scheduled runs, or force flag
is_main_push=$([[ "$EVENT_NAME" == "push" && "$GIT_REF" == "refs/heads/main" ]] && echo true || echo false)
is_schedule=$([[ "$EVENT_NAME" == "schedule" ]] && echo true || echo false)
is_force=$([[ "$EVENT_NAME" == "workflow_dispatch" && "$FORCE_LATEST" == "true" ]] && echo true || echo false)

if [[ "$is_main_push" == "true" || "$is_schedule" == "true" || "$is_force" == "true" ]]; then
	TAGS="${TAGS},${IMAGE_BASE}:latest"
	echo "push_latest=true" >>"$GITHUB_OUTPUT"
else
	echo "push_latest=false" >>"$GITHUB_OUTPUT"
fi

# Add PR-specific tag for pull requests
if [[ "$IS_PR" == "true" && -n "$PR_NUMBER" ]]; then
	TAGS="${TAGS},${IMAGE_BASE}:pr-${PR_NUMBER}"
	echo "pr_tag=${IMAGE_BASE}:pr-${PR_NUMBER}" >>"$GITHUB_OUTPUT"
fi

echo "tags=${TAGS}" >>"$GITHUB_OUTPUT"
echo "Generated tags: ${TAGS}"
