#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Push tools image tags to container registry with error handling.

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Push tools image tags to container registry with per-tag error handling.

Usage:
  scripts/ci/tools-image-push.sh

Environment Variables (required):
  TAGS   Comma-separated list of image tags to push

The script pushes each tag individually, tracking successes and failures.
All tags are attempted even if some fail. Exits non-zero if any tag fails.

Example:
  TAGS=ghcr.io/lgtm-hq/lintro-tools:latest,ghcr.io/lgtm-hq/lintro-tools:v1.0 \
    ./scripts/ci/tools-image-push.sh
EOF
	exit 0
fi

if [[ -z "${TAGS:-}" ]]; then
	echo "::error::TAGS environment variable is required"
	exit 1
fi

IFS=',' read -r -a tags <<<"$TAGS"
failed_tags=()
succeeded_tags=()

for tag in "${tags[@]}"; do
	# Trim leading/trailing whitespace
	tag="${tag#"${tag%%[![:space:]]*}"}"
	tag="${tag%"${tag##*[![:space:]]}"}"

	# Skip empty tags
	[[ -z "$tag" ]] && continue

	echo "Pushing ${tag}..."
	if docker push "${tag}"; then
		succeeded_tags+=("$tag")
	else
		echo "::warning::Failed to push ${tag}"
		failed_tags+=("$tag")
	fi
done

echo "Succeeded: ${#succeeded_tags[@]}/${#tags[@]} tags"

if [[ ${#failed_tags[@]} -gt 0 ]]; then
	echo "::error::Failed to push tags: ${failed_tags[*]}"
	exit 1
fi
