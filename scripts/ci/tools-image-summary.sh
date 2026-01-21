#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Generate GitHub step summary for the tools image build.

set -euo pipefail

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
} >> "$GITHUB_STEP_SUMMARY"

if [[ "$PUSH_LATEST" == "true" ]]; then
    echo ":white_check_mark: **:latest tag updated**" >> "$GITHUB_STEP_SUMMARY"
fi

if [[ -n "$PR_TAG" ]]; then
    echo ":test_tube: **PR testing tag:** \`${PR_TAG}\`" >> "$GITHUB_STEP_SUMMARY"
fi
