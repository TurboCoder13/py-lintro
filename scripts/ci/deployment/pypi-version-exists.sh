#!/usr/bin/env bash
set -euo pipefail

# pypi-version-exists.sh
# Check if a given version for a project exists on PyPI.
# Outputs: exists=true/false to GITHUB_OUTPUT

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
	echo "Usage: scripts/ci/pypi-version-exists.sh <project-name> <version>"
	echo ""
	echo "Query PyPI JSON API to check if version exists."
	exit 0
fi

PROJECT=${1:-}
VERSION=${2:-}
if [ -z "$PROJECT" ] || [ -z "$VERSION" ]; then
	echo "project name and version are required" >&2
	exit 2
fi

URL="https://pypi.org/pypi/${PROJECT}/json"

if curl -fsSL "$URL" -o /tmp/pypi.json 2>/dev/null; then
	if jq -e --arg v "$VERSION" '.releases[$v] | length > 0' /tmp/pypi.json >/dev/null 2>&1; then
		echo "exists=true" | tee /dev/stderr
		[ -n "${GITHUB_OUTPUT:-}" ] && echo "exists=true" >>"$GITHUB_OUTPUT"
		exit 0
	fi
fi

echo "exists=false" | tee /dev/stderr
[ -n "${GITHUB_OUTPUT:-}" ] && echo "exists=false" >>"$GITHUB_OUTPUT"
exit 0
