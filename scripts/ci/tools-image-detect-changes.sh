#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# For license details, see the repository root LICENSE file.
#
# Detect tool file changes that require a fresh tools image build.
# Used by resolve-tools-image action.
#
# Required environment variables:
#   GITHUB_EVENT_NAME     - "push" or "pull_request"
#   GITHUB_OUTPUT         - Path to GitHub outputs file
# Required for pull_request:
#   PR_BASE_SHA           - Base commit SHA for PR
#   PR_HEAD_SHA           - Head commit SHA for PR
# Required for push:
#   GITHUB_EVENT_BEFORE   - Before SHA for push event

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Detect tool file changes that require a fresh tools image build.

Usage:
  scripts/ci/tools-image-detect-changes.sh

Environment Variables (required):
  GITHUB_EVENT_NAME   GitHub event name (push or pull_request)
  GITHUB_OUTPUT       Path to GitHub output file

Environment Variables (for pull_request):
  PR_BASE_SHA         Base commit SHA for PR
  PR_HEAD_SHA         Head commit SHA for PR

Environment Variables (for push):
  GITHUB_EVENT_BEFORE Before SHA for push event

Outputs (to GITHUB_OUTPUT):
  tools_changed       "true" if tool files changed, "false" otherwise

Example:
  GITHUB_EVENT_NAME=push GITHUB_OUTPUT=/tmp/out GITHUB_EVENT_BEFORE=abc123 \
    ./scripts/ci/tools-image-detect-changes.sh
EOF
	exit 0
fi

: "${GITHUB_EVENT_NAME:?GITHUB_EVENT_NAME is required}"
: "${GITHUB_OUTPUT:?GITHUB_OUTPUT is required}"

# Define tool-related file patterns that affect image CONTENT
# Note: scripts/ci/tools-image-*.sh are CI helpers (tags, verify, summary)
# and don't affect image content, so they're not included here
TOOL_PATTERNS=(
	"Dockerfile.tools"
	"scripts/utils/install-tools.sh"
	"package.json"
	"lintro/_tool_versions.py"
	"lintro/tools/manifest.json"
)

tools_changed="false"

if [[ "$GITHUB_EVENT_NAME" == "pull_request" ]]; then
	: "${PR_BASE_SHA:?PR_BASE_SHA is required for pull_request events}"
	: "${PR_HEAD_SHA:?PR_HEAD_SHA is required for pull_request events}"

	# For PRs, compare base to head
	echo "Checking for tool file changes in PR..."
	changed_files=$(git diff --name-only "$PR_BASE_SHA" "$PR_HEAD_SHA" \
		2>/dev/null || echo "")

	for pattern in "${TOOL_PATTERNS[@]}"; do
		if echo "$changed_files" | grep -q "$pattern"; then
			echo "Found tool file change matching: $pattern"
			tools_changed="true"
			break
		fi
	done
elif [[ "$GITHUB_EVENT_NAME" == "push" ]]; then
	# For push events, check if tool files changed in the pushed commits
	echo "Checking for tool file changes in push..."
	# Get the before/after from the push event
	BEFORE_SHA="${GITHUB_EVENT_BEFORE:-}"
	ZERO_SHA="0000000000000000000000000000000000000000"
	if [[ -n "$BEFORE_SHA" ]] && [[ "$BEFORE_SHA" != "$ZERO_SHA" ]]; then
		changed_files=$(git diff --name-only "$BEFORE_SHA" HEAD \
			2>/dev/null || echo "")
		for pattern in "${TOOL_PATTERNS[@]}"; do
			if echo "$changed_files" | grep -q "$pattern"; then
				echo "Found tool file change matching: $pattern"
				tools_changed="true"
				break
			fi
		done
	fi
else
	echo "Event type: $GITHUB_EVENT_NAME, using stable image"
fi

echo "tools_changed=${tools_changed}" >>"$GITHUB_OUTPUT"
echo "Tools changed: ${tools_changed}"
