#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# For license details, see the repository root LICENSE file.
#
# tools-image-update-digest.sh - Update pinned tools image digest in repository files
#
# This script updates the tools image digest in:
#   - Dockerfile (TOOLS_IMAGE ARG)
#   - .github/actions/resolve-tools-image/action.yml (stable-image default)
#
# Usage:
#   ./scripts/ci/tools-image-update-digest.sh <new-digest>
#
# Example:
#   ./scripts/ci/tools-image-update-digest.sh sha256:abc123...

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Files to update
DOCKERFILE="$PROJECT_ROOT/Dockerfile"
ACTION_YML="$PROJECT_ROOT/.github/actions/resolve-tools-image/action.yml"

# Image pattern to match (without digest)
IMAGE_PATTERN="ghcr.io/lgtm-hq/lintro-tools:latest"

# Show help if requested
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Usage: tools-image-update-digest.sh <new-digest>

Update the pinned tools image digest in repository files.

This script updates the tools image digest in:
  - Dockerfile (TOOLS_IMAGE ARG)
  - .github/actions/resolve-tools-image/action.yml (stable-image default)

Arguments:
  new-digest    The new digest to use (e.g., sha256:abc123...)

Example:
  ./scripts/ci/tools-image-update-digest.sh sha256:b3940578b3fa10215d2ba4accba89250753360ec6f34cebe2dc588694084dad4
EOF
	exit 0
fi

usage() {
	echo "Usage: $0 <new-digest>"
	echo ""
	echo "Update the pinned tools image digest in repository files."
	echo ""
	echo "Arguments:"
	echo "  new-digest    The new digest to use (e.g., sha256:abc123...)"
	echo ""
	echo "Example:"
	echo "  $0 sha256:b3940578b3fa10215d2ba4accba89250753360ec6f34cebe2dc588694084dad4"
	exit 1
}

# Validate arguments
if [[ $# -ne 1 ]]; then
	usage
fi

NEW_DIGEST="$1"

# Validate digest format
if [[ ! "$NEW_DIGEST" =~ ^sha256:[a-f0-9]{64}$ ]]; then
	echo "ERROR: Invalid digest format. Expected sha256:<64-hex-chars>" >&2
	echo "       Got: $NEW_DIGEST" >&2
	exit 1
fi

# Check that files exist
if [[ ! -f "$DOCKERFILE" ]]; then
	echo "ERROR: Dockerfile not found at $DOCKERFILE" >&2
	exit 1
fi

if [[ ! -f "$ACTION_YML" ]]; then
	echo "ERROR: action.yml not found at $ACTION_YML" >&2
	exit 1
fi

# Regex pattern to match the image with any digest
# Matches: ghcr.io/lgtm-hq/lintro-tools:latest@sha256:<64-hex-chars>
DIGEST_PATTERN="(${IMAGE_PATTERN}@sha256:)[a-f0-9]{64}"
REPLACEMENT="\1${NEW_DIGEST#sha256:}"

echo "Updating tools image digest to: $NEW_DIGEST"

# Update Dockerfile
echo "  Updating $DOCKERFILE..."
if grep -qE "$DIGEST_PATTERN" "$DOCKERFILE"; then
	if [[ "$OSTYPE" == "darwin"* ]]; then
		# macOS sed requires empty string for -i
		sed -i '' -E "s|${DIGEST_PATTERN}|${REPLACEMENT}|g" "$DOCKERFILE"
	else
		sed -i -E "s|${DIGEST_PATTERN}|${REPLACEMENT}|g" "$DOCKERFILE"
	fi
	echo "    ✓ Updated Dockerfile"
else
	echo "ERROR: Pattern not found in Dockerfile" >&2
	echo "       Expected: ${IMAGE_PATTERN}@sha256:<digest>" >&2
	echo "       File: $DOCKERFILE" >&2
	exit 1
fi

# Update action.yml
echo "  Updating $ACTION_YML..."
if grep -qE "$DIGEST_PATTERN" "$ACTION_YML"; then
	if [[ "$OSTYPE" == "darwin"* ]]; then
		sed -i '' -E "s|${DIGEST_PATTERN}|${REPLACEMENT}|g" "$ACTION_YML"
	else
		sed -i -E "s|${DIGEST_PATTERN}|${REPLACEMENT}|g" "$ACTION_YML"
	fi
	echo "    ✓ Updated action.yml"
else
	echo "ERROR: Pattern not found in action.yml" >&2
	echo "       Expected: ${IMAGE_PATTERN}@sha256:<digest>" >&2
	echo "       File: $ACTION_YML" >&2
	exit 1
fi

# Verify updates
echo ""
echo "Verification:"
echo "  Dockerfile:"
grep -n "TOOLS_IMAGE=" "$DOCKERFILE" | head -1 || echo "    (TOOLS_IMAGE not found)"
echo "  action.yml:"
grep -n "stable-image" "$ACTION_YML" | grep -v description | head -1 || echo "    (stable-image not found)"

echo ""
echo "Done."
