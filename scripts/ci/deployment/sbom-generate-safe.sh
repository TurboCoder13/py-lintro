#!/usr/bin/env bash
#
# Generate SBOMs safely with error handling
# Consolidates the common SBOM generation pattern used in workflows
#
# Usage: scripts/ci/sbom-generate-safe.sh [--help]

set -euo pipefail

show_help() {
	cat <<EOF
Generate SBOMs safely with error handling

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --help      Show this help message

DESCRIPTION:
    Consolidates the common SBOM generation pattern used in workflows.
    Generates SBOMs with standard formats and handles errors gracefully.

EXAMPLES:
    $0
EOF
}

# Check for help flag before sourcing utils
if [[ "${1:-}" == "--help" ]]; then
	show_help
	exit 0
fi

# Source common utilities for consistent logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
# SC1091: path is dynamically constructed, file exists at runtime
# shellcheck source=../../utils/utils.sh disable=SC1091
source "${SCRIPT_DIR}/../../utils/utils.sh"

main() {
	log_info "Generating SBOMs with standard formats"

	# Use the existing sbom-generate.sh with standard parameters
	# The || true handles cases where SBOM generation might fail non-critically
	if bash "${SCRIPT_DIR}/sbom-generate.sh" \
		--skip-fetch \
		--format cyclonedx-1.6 \
		--format spdx-2.3 \
		--name "py-lintro-sbom" \
		--alias project; then
		log_success "SBOM generation completed successfully"
	else
		log_warning "SBOM generation completed with warnings/errors (non-critical)"
	fi
}

main "$@"
