#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# For license details, see the repository root LICENSE file.
#
# Wait for the tools-image workflow to complete.
# Used by resolve-tools-image action when tool files change.
#
# Required environment variables:
#   GH_TOKEN        - GitHub token for API access
#   COMMIT_SHA      - Commit SHA to wait for (for push events)
#   EVENT_TYPE      - "push" or "pull_request"
# Optional (for pull_request event):
#   PR_HEAD_SHA     - PR head commit SHA
#   PR_NUMBER       - PR number

set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN is required}"
: "${COMMIT_SHA:?COMMIT_SHA is required}"
: "${EVENT_TYPE:?EVENT_TYPE is required (push or pull_request)}"

# Wait for the tools-image workflow to complete (max 45 minutes)
# Tools image build can take up to 30 min, so allow plenty of time
MAX_ATTEMPTS=270
ATTEMPT=0

echo "Waiting for tools-image workflow (event: $EVENT_TYPE)..."

while [[ $ATTEMPT -lt $MAX_ATTEMPTS ]]; do
	STATUS=""

	if [[ "$EVENT_TYPE" == "pull_request" ]]; then
		# For PRs, try branch-based lookup first, then commit SHA
		: "${PR_HEAD_SHA:?PR_HEAD_SHA is required for pull_request events}"
		: "${PR_NUMBER:?PR_NUMBER is required for pull_request events}"

		# Use head SHA to find the correct workflow run
		# shellcheck disable=SC2016
		JQ_FILTER='.[] | select(.headSha == "'"$PR_HEAD_SHA"'")
            | "\(.status) \(.conclusion)"'
		STATUS=$(gh run list \
			--workflow "Build - Tools Image" \
			--branch "pull/$PR_NUMBER/head" \
			--json status,conclusion,headSha \
			--jq "$JQ_FILTER" \
			2>/dev/null | head -1 || echo "not_found")

		# If no run found by branch, try by commit SHA directly
		if [[ -z "$STATUS" ]] || [[ "$STATUS" == "not_found" ]]; then
			STATUS=$(gh run list \
				--workflow "Build - Tools Image" \
				--commit "$PR_HEAD_SHA" \
				--json status,conclusion \
				--jq '.[0] | "\(.status) \(.conclusion)"' 2>/dev/null ||
				echo "not_found")
		fi
	else
		# For push events, use commit SHA
		STATUS=$(gh run list \
			--workflow "Build - Tools Image" \
			--commit "$COMMIT_SHA" \
			--json status,conclusion \
			--jq '.[0] | "\(.status) \(.conclusion)"' 2>/dev/null ||
			echo "not_found")
	fi

	echo "Attempt $((ATTEMPT + 1))/$MAX_ATTEMPTS: status: $STATUS"

	if [[ "$STATUS" == "completed success" ]]; then
		echo "Tools image workflow completed successfully!"
		exit 0
	elif [[ "$STATUS" == "completed failure" ]] ||
		[[ "$STATUS" == "completed cancelled" ]]; then
		echo "::error::Tools image workflow failed or was cancelled"
		exit 1
	fi

	ATTEMPT=$((ATTEMPT + 1))
	sleep 10
done

echo "::error::Timed out waiting for tools-image workflow (45 min)"
exit 1
