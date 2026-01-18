#!/usr/bin/env bash
set -euo pipefail

# install-uv.sh - Install uv from GitHub Releases if not available
# Single Responsibility: Only handle uv installation

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
	cat <<'EOF'
Install uv from GitHub Releases if not already available.

Usage:
  scripts/utils/install-uv.sh [--help|-h] [--dry-run] [--verbose]

Options:
  --help, -h    Show this help message
  --dry-run     Show what would be done without executing
  --verbose     Enable verbose output

Environment Variables:
  UV_VERSION    Specific uv version to install (default: latest)
  GITHUB_TOKEN  GitHub token for API access
EOF
	exit 0
fi

DRY_RUN=0
VERBOSE=0

# Parse arguments
while [[ $# -gt 0 ]]; do
	case $1 in
	--dry-run)
		DRY_RUN=1
		shift
		;;
	--verbose)
		VERBOSE=1
		shift
		;;
	*)
		echo "Unknown argument: $1" >&2
		exit 1
		;;
	esac
done

log_info() {
	echo "[install-uv] $*"
}

log_verbose() {
	[ $VERBOSE -eq 1 ] && echo "[install-uv] [verbose] $*" || true
}

# Check if uv is already available
if command -v uv >/dev/null 2>&1; then
	log_info "uv is already available: $(command -v uv)"
	log_verbose "Version: $(uv --version 2>/dev/null || echo 'unknown')"
	exit 0
fi

log_info "uv not found; installing from GitHub Releases"

if [ $DRY_RUN -eq 1 ]; then
	log_info "[DRY-RUN] Would install uv from GitHub Releases"
	exit 0
fi

# Ensure gh CLI is available
if ! command -v gh >/dev/null 2>&1; then
	echo "[install-uv] ERROR: gh CLI is required to install uv from GitHub releases" >&2
	exit 1
fi

# Set GH_TOKEN for gh CLI from GITHUB_TOKEN if available
if [ -n "${GITHUB_TOKEN:-}" ]; then
	export GH_TOKEN="${GITHUB_TOKEN}"
fi

# Platform validation
tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT
os="$(uname -s | tr '[:upper:]' '[:lower:]')"
arch="$(uname -m)"

if [ "${os}" != "linux" ] || ! echo "${arch}" | grep -Eq '^(x86_64|amd64)$'; then
	echo "[install-uv] ERROR: Unsupported platform ${os}/${arch}" >&2
	echo "[install-uv] Currently only linux/x86_64 is supported" >&2
	exit 1
fi

# Resolve version
tag_name="${UV_VERSION:-$(gh release view -R astral-sh/uv --json tagName --jq '.tagName' 2>/dev/null || true)}"
if [ -z "${tag_name}" ]; then
	echo "[install-uv] ERROR: Unable to resolve uv release tag" >&2
	echo "[install-uv] Try setting UV_VERSION environment variable" >&2
	exit 1
fi

log_info "Installing uv ${tag_name}"
log_verbose "Target platform: ${os}/${arch}"

# Download with fallback and retry
primary="uv-x86_64-unknown-linux-gnu.tar.gz"
fallback="uv-x86_64-unknown-linux-musl.tar.gz"
download_success=0
max_retries=3
assets=("${primary}" "${fallback}")

for asset in "${assets[@]}"; do
	for attempt in $(seq 1 $max_retries); do
		log_verbose "Attempting to download ${asset} (attempt ${attempt}/${max_retries})"
		if gh release download "${tag_name}" -R astral-sh/uv -p "${asset}" -O "${tmpdir}/uv.tgz"; then
			download_success=1
			log_info "Successfully downloaded ${asset}"
			break 2
		else
			if [ $attempt -lt $max_retries ]; then
				sleep_time=$((attempt * 2))
				log_verbose "Download failed, retrying in ${sleep_time} seconds..."
				sleep $sleep_time
			fi
		fi
	done
done

if [ $download_success -eq 0 ]; then
	echo "[install-uv] ERROR: Failed to download uv for ${tag_name}" >&2
	exit 1
fi

# Extract and install
uv_path_in_tgz="$(tar -tzf "${tmpdir}/uv.tgz" | grep -E '(^|/)uv$' | head -n1 || true)"
if [ -z "${uv_path_in_tgz}" ]; then
	echo "[install-uv] ERROR: uv binary not found in archive" >&2
	exit 1
fi

tar -C "${tmpdir}" -xzf "${tmpdir}/uv.tgz" "${uv_path_in_tgz}"

# Install to user bin, fall back to system
if install -m 0755 "${tmpdir}/${uv_path_in_tgz}" "$HOME/.local/bin/uv" 2>/dev/null; then
	log_info "Installed uv to $HOME/.local/bin/uv"
	# Add to PATH for current session
	if [ -n "${GITHUB_PATH:-}" ] && [ -d "$HOME/.local/bin" ]; then
		echo "$HOME/.local/bin" >>"$GITHUB_PATH"
	fi
else
	sudo install -m 0755 "${tmpdir}/${uv_path_in_tgz}" /usr/local/bin/uv
	log_info "Installed uv to /usr/local/bin/uv (with sudo)"
fi

# Verify installation
if ! command -v uv >/dev/null 2>&1; then
	echo "[install-uv] ERROR: Failed to install uv properly" >&2
	exit 1
fi

log_info "uv installation complete: $(uv --version)"
