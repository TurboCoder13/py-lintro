#!/usr/bin/env bash
# wait-for-pypi.sh
# Wait for a package version to be available on PyPI

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../utils/utils.sh
source "$SCRIPT_DIR/../../utils/utils.sh"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Wait for a package version to be available on PyPI.

Usage: wait-for-pypi.sh <package-name> <version> [max-attempts] [delay-seconds]

Arguments:
  package-name   The package name on PyPI (e.g., lintro)
  version        The version to wait for (e.g., 1.0.0)
  max-attempts   Maximum number of attempts (default: 30)
  delay-seconds  Delay between attempts in seconds (default: 10)

Examples:
  wait-for-pypi.sh lintro 1.0.0
  wait-for-pypi.sh lintro 1.0.0 20 5
EOF
	exit 0
fi

PACKAGE_NAME="${1:?Package name is required}"
VERSION="${2:?Version is required}"
MAX_ATTEMPTS="${3:-30}"
DELAY_SECONDS="${4:-10}"

PYPI_URL="https://pypi.org/pypi/${PACKAGE_NAME}/${VERSION}/json"

# Check if sdist is available in the PyPI response
# Uses jq for robust JSON parsing if available, falls back to grep
has_sdist() {
	local response="$1"
	if command -v jq &>/dev/null; then
		echo "$response" | jq -e '.urls[] | select(.packagetype == "sdist")' &>/dev/null
	else
		# Pattern handles both pretty-printed and compact JSON
		echo "$response" | grep -E -q '"packagetype"[[:space:]]*:[[:space:]]*"sdist"'
	fi
}

log_info "Waiting for ${PACKAGE_NAME} ${VERSION} to be available on PyPI..."
log_info "URL: ${PYPI_URL}"

for i in $(seq 1 "$MAX_ATTEMPTS"); do
	RESPONSE=$(curl -sf "$PYPI_URL" 2>/dev/null || echo "")

	if [[ -z "$RESPONSE" ]]; then
		log_info "Attempt ${i}/${MAX_ATTEMPTS}: Package metadata not yet available, waiting ${DELAY_SECONDS}s..."
		sleep "$DELAY_SECONDS"
		continue
	fi

	# Check that the sdist (source distribution) is available, not just metadata
	# This prevents race conditions where metadata exists but files aren't indexed
	if has_sdist "$RESPONSE"; then
		log_success "Package ${PACKAGE_NAME} ${VERSION} is available on PyPI (sdist confirmed)"
		exit 0
	fi

	log_info "Attempt ${i}/${MAX_ATTEMPTS}: Metadata exists but sdist not yet indexed, waiting ${DELAY_SECONDS}s..."
	sleep "$DELAY_SECONDS"
done

log_error "Timeout waiting for ${PACKAGE_NAME} ${VERSION} sdist on PyPI after ${MAX_ATTEMPTS} attempts"
exit 1
