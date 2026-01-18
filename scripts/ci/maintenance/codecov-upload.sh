#!/usr/bin/env bash
set -euo pipefail

# Download and run the Codecov uploader in a hardened, pinned manner.
#
# Required env vars:
#   CODECOV_VERSION  - release tag in codecov/uploader (e.g., v0.7.7)
#   CODECOV_SHA256   - expected SHA256 checksum (optional, recommended)
# Optional env vars:
#   CODECOV_FILES    - coverage file path(s). Default: ./coverage.xml
#   CODECOV_FLAGS    - flags to tag this upload (e.g., python-3.13)
#   CODECOV_TOKEN    - repository token, if required
#   CODECOV_ASSET    - uploader asset name. Default: codecov-linux
#   CODECOV_CHECKSUM_ASSET - checksum asset name. Default: codecov-linux.sha256
#
# This script avoids curl/wget; it uses GitHub CLI to fetch the pinned
# release asset, verifies the checksum, and executes the uploader.

show_help() {
	cat <<'USAGE'
Usage: scripts/ci/codecov-upload.sh [--help]

Securely download and run the Codecov uploader via GitHub CLI.

Environment variables:
  CODECOV_VERSION          Release tag (e.g., v0.7.7). Required.
  CODECOV_SHA256           Expected SHA256 checksum (optional). If not set,
                           the script will attempt to download
                           CODECOV_CHECKSUM_ASSET and verify against it.
  CODECOV_FILES            Coverage file(s). Default: ./coverage.xml
  CODECOV_FLAGS            Flags to tag this upload (e.g., python-3.13)
  CODECOV_TOKEN            Repository token, if required by your setup
  CODECOV_ASSET            Uploader asset name. Default: codecov-linux
  CODECOV_CHECKSUM_ASSET   Checksum asset name. Default: codecov-linux.sha256

This script avoids using curl/wget and transitive GitHub Actions. It relies on
GitHub CLI to fetch a pinned uploader asset and verifies its checksum.
USAGE
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	show_help
	exit 0
fi

require_env() {
	local name="$1"
	if [[ -z "${!name:-}" ]]; then
		echo "Missing required environment variable: ${name}" >&2
		exit 2
	fi
}

command -v gh >/dev/null 2>&1 || {
	echo "GitHub CLI (gh) is required but not installed on this runner." >&2
	exit 2
}

# Set GH_TOKEN for gh CLI from GITHUB_TOKEN if available
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
	export GH_TOKEN="${GITHUB_TOKEN}"
fi

require_env CODECOV_VERSION
CODECOV_FILES="${CODECOV_FILES:-./coverage.xml}"
CODECOV_ASSET="${CODECOV_ASSET:-codecov-linux}"
CODECOV_CHECKSUM_ASSET="${CODECOV_CHECKSUM_ASSET:-codecov-linux.sha256}"

echo "Downloading Codecov uploader ${CODECOV_VERSION} via gh…" >&2
gh release download "${CODECOV_VERSION}" -R codecov/uploader -p "${CODECOV_ASSET}" -O codecov

# Try to get checksum from provided env or from release asset
ACTUAL_SHA256=""
if [[ -n "${CODECOV_SHA256:-}" ]]; then
	EXPECTED_SHA256="${CODECOV_SHA256}"
else
	echo "Downloading checksum asset ${CODECOV_CHECKSUM_ASSET}…" >&2
	gh release download "${CODECOV_VERSION}" -R codecov/uploader -p "${CODECOV_CHECKSUM_ASSET}" -O codecov.sha256 || true
fi

echo "Verifying uploader checksum…" >&2

# Compute actual digest of the downloaded uploader (saved as 'codecov')
if command -v sha256sum >/dev/null 2>&1; then
	ACTUAL_SHA256="$(sha256sum codecov | awk '{print $1}')"
elif command -v shasum >/dev/null 2>&1; then
	ACTUAL_SHA256="$(shasum -a 256 codecov | awk '{print $1}')"
else
	echo "No SHA256 tool available (sha256sum/shasum)." >&2
	exit 2
fi

# Determine expected digest either from env or from downloaded checksum asset
if [[ -n "${EXPECTED_SHA256:-}" ]]; then
	EXPECTED_FROM_ASSET="${EXPECTED_SHA256}"
elif [[ -f codecov.sha256 ]]; then
	# The checksum file may reference a different filename (e.g., codecov-linux)
	# Extract the first field which is the digest regardless of filename.
	EXPECTED_FROM_ASSET="$(awk 'NF{print $1; exit}' codecov.sha256)"
fi

if [[ -n "${EXPECTED_FROM_ASSET:-}" ]]; then
	if [[ "${ACTUAL_SHA256}" != "${EXPECTED_FROM_ASSET}" ]]; then
		echo "Checksum mismatch for Codecov uploader:" >&2
		echo "  expected: ${EXPECTED_FROM_ASSET}" >&2
		echo "  actual:   ${ACTUAL_SHA256}" >&2
		exit 2
	fi
else
	echo "Warning: No checksum provided or downloadable checksum asset missing." >&2
	echo "Proceeding without checksum validation (not recommended)." >&2
fi

chmod +x codecov

echo "Running Codecov uploader…" >&2
ARGS=(-f "${CODECOV_FILES}")

if [[ -n "${CODECOV_FLAGS:-}" ]]; then
	ARGS+=(-F "${CODECOV_FLAGS}")
fi

if [[ -n "${CODECOV_TOKEN:-}" ]]; then
	ARGS+=(-t "${CODECOV_TOKEN}")
fi

./codecov "${ARGS[@]}"

echo "Codecov upload step completed." >&2
