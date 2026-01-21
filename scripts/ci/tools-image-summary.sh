#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Generate GitHub step summary for the tools image build.

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Generate GitHub step summary for the tools image build.

Usage:
  scripts/ci/tools-image-summary.sh

Environment Variables (required):
  GITHUB_STEP_SUMMARY  Path to GitHub step summary file
  TAGS                 Comma-separated list of image tags

Environment Variables (optional):
  PUSH_LATEST          Whether :latest was pushed (default: false)
  PR_TAG               PR-specific tag if applicable

Example:
  GITHUB_STEP_SUMMARY=/tmp/summary.md TAGS="ghcr.io/foo:sha-abc123" \
    ./scripts/ci/tools-image-summary.sh
EOF
	exit 0
fi

: "${GITHUB_STEP_SUMMARY:?GITHUB_STEP_SUMMARY must be set}"
: "${TAGS:?TAGS must be set}"

PUSH_LATEST="${PUSH_LATEST:-false}"
PR_TAG="${PR_TAG:-}"

{
	echo "## Tools Image Build Summary"
	echo ""
	echo "**Tags generated:**"
	echo '```'
	echo "$TAGS" | tr ',' '\n'
	echo '```'
	echo ""
} >>"$GITHUB_STEP_SUMMARY"

if [[ "$PUSH_LATEST" == "true" ]]; then
	echo ":white_check_mark: **:latest tag updated**" >>"$GITHUB_STEP_SUMMARY"
fi

if [[ -n "$PR_TAG" ]]; then
	echo ":test_tube: **PR testing tag:** \`${PR_TAG}\`" >>"$GITHUB_STEP_SUMMARY"
fi
