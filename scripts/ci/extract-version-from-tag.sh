#!/usr/bin/env bash
# extract-version-from-tag.sh
# Extract version from GITHUB_REF or GITHUB_REF_NAME
# Strips the 'v' prefix if present

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../utils/utils.sh
source "$SCRIPT_DIR/../utils/utils.sh"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Extract version from git tag reference.

Usage: extract-version-from-tag.sh

Env:
  GITHUB_REF       Git reference (e.g., refs/tags/v1.0.0)
  GITHUB_REF_NAME  Git reference name (e.g., v1.0.0)
  GITHUB_OUTPUT    GitHub Actions output file (optional)

Output:
  Prints version to stdout
  Sets 'version' in GITHUB_OUTPUT if available
EOF
	exit 0
fi

# Try GITHUB_REF_NAME first (preferred), then fall back to GITHUB_REF
if [[ -n "${GITHUB_REF_NAME:-}" ]]; then
	VERSION="${GITHUB_REF_NAME#v}"
elif [[ -n "${GITHUB_REF:-}" ]]; then
	VERSION="${GITHUB_REF#refs/tags/}"
	VERSION="${VERSION#v}"
else
	log_error "Neither GITHUB_REF nor GITHUB_REF_NAME is set"
	exit 1
fi

log_info "Extracted version: $VERSION"

# Set GitHub Actions output if available
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
	echo "version=$VERSION" >>"$GITHUB_OUTPUT"
	log_success "Version set in GITHUB_OUTPUT"
fi

echo "$VERSION"
