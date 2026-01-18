#!/usr/bin/env bash
set -euo pipefail

# detect-changes.sh
#
# Usage:
#   scripts/ci/detect-changes.sh [--help]
#
# Detect whether the working tree has changes compared to HEAD and write a
# GitHub Actions output variable named 'has_changes' to $GITHUB_OUTPUT.
#
# This script is intended for use within GitHub Actions jobs. When run
# outside of Actions, it will still print a human-friendly message and exit 0
# with no side effects if $GITHUB_OUTPUT is not set.

show_help() {
	cat <<'USAGE'
Usage: scripts/ci/detect-changes.sh

Detect repository changes and set has_changes output for GitHub Actions.

Outputs (via GITHUB_OUTPUT):
  has_changes=true|false
USAGE
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	show_help
	exit 0
fi

if git diff --quiet --exit-code; then
	echo "No changes detected."
	if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
		echo "has_changes=false" >>"$GITHUB_OUTPUT"
	fi
else
	echo "Changes detected."
	if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
		echo "has_changes=true" >>"$GITHUB_OUTPUT"
	fi
fi
