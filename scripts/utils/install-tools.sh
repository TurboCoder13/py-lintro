#!/usr/bin/env bash
set -euo pipefail

# install-tools.sh - Simplified tool installer for lintro
#
# This script installs all external tools required by lintro.
# It uses consistent installation methods and is optimized for Docker environments.
#
# Usage:
#   ./scripts/install-tools.sh [--help] [--dry-run] [--verbose] [--local|--docker]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# SC1091: path is dynamically constructed, file exists at runtime
# shellcheck source=utils.sh disable=SC1091
source "$SCRIPT_DIR/utils.sh"

# Get tool version from lintro/_tool_versions.py
# This module is the single source of truth for all tool versions
# Uses runpy.run_path() to execute the file directly without package installation
get_tool_version() {
	local tool_name="$1"
	local version
	version=$(python3 -c "
import runpy
import sys

versions = runpy.run_path('$PROJECT_ROOT/lintro/_tool_versions.py')
version = versions['TOOL_VERSIONS'].get('$tool_name')
if version:
    print(version)
else:
    sys.exit(1)
" 2>/dev/null)
	if [ -z "$version" ]; then
		echo "ERROR: Version for '$tool_name' not found in lintro/_tool_versions.py" >&2
		return 1
	fi
	echo "$version"
}

# Show help if requested
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	cat <<'EOF'
Usage: install-tools.sh [--help] [--dry-run] [--verbose] [--local|--docker]

Tool Installation Script
Installs all required linting and formatting tools.

Options:
  --help, -h     Show this help message
  --dry-run      Show what would be done without executing
  --verbose      Enable verbose output
  --local        Install tools locally (default)
  --docker       Install tools system-wide for Docker

This script installs:
  - Ruff (Python linter and formatter)
  - Pydoclint (docstring linter)
  - Black (Python formatter; runs as a post-check in Lintro)
  - Prettier (code formatter)
  - Markdownlint-cli2 (Markdown linter)
  - Yamllint (YAML linter)
  - Hadolint (Dockerfile linter)
  - Actionlint (GitHub Actions workflow linter)
  - Bandit (Python security linter)
  - Mypy (Python static type checker)
  - Clippy (Rust linter; requires Rust toolchain)
  - Rustfmt (Rust formatter; requires Rust toolchain)
  - Cargo-audit (Rust dependency vulnerability scanner; requires Rust toolchain)
  - Semgrep (Security scanner)
  - ShellCheck (Shell script linter)
  - shfmt (Shell script formatter)
  - SQLFluff (SQL linter and formatter)
  - Taplo (TOML linter and formatter)
  - TypeScript (TypeScript compiler and type checker)

Use this script to set up a complete development environment.
EOF
	exit 0
fi

# Global flags
DRY_RUN=0
# Note: VERBOSE may already be set by utils.sh, so use default
VERBOSE="${VERBOSE:-0}"

# Parse flags and collect positional args
POSITIONAL=()
while [[ $# -gt 0 ]]; do
	case "$1" in
	--dry-run)
		DRY_RUN=1
		shift
		;;
	--verbose)
		VERBOSE=1
		shift
		;;
	--help | -h)
		# Already handled above
		shift
		;;
	*)
		POSITIONAL+=("$1")
		shift
		;;
	esac
done
set -- "${POSITIONAL[@]:-}"

# Script-specific logging (prefixed)
install_log() { echo "[install-tools] $*"; }

# Helper function to ensure bun is installed
# Returns 0 on success, non-zero on failure (does not call exit)
ensure_bun_installed() {
	if command -v bun &>/dev/null; then
		return 0
	fi

	echo -e "${YELLOW}bun not found, trying to install...${NC}"

	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install bun via curl"
		return 0
	fi

	# Install bun via official installer (works on Linux and macOS)
	# Justification: Official bun installer from trusted source (bun.sh)
	# nosemgrep: curl-pipe-bash
	if curl -fsSL https://bun.sh/install | bash; then
		# Source bun environment
		if [ -f "$HOME/.bun/bin/bun" ]; then
			export BUN_INSTALL="$HOME/.bun"
			export PATH="$BUN_INSTALL/bin:$PATH"
		fi
		return 0
	fi

	# Try Homebrew on macOS as fallback
	if command -v brew &>/dev/null; then
		echo -e "${YELLOW}Trying Homebrew for bun...${NC}"
		if brew install oven-sh/bun/bun; then
			return 0
		fi
	fi

	echo -e "${RED}✗ Cannot install bun automatically. Please install bun manually: https://bun.sh${NC}"
	return 1
}

# Simple downloader with retries/backoff
download_with_retries() {
	local url="$1"
	shift
	local out="$1"
	shift
	local attempts=${1:-3}
	local delay=0.5
	local i
	for ((i = 1; i <= attempts; i++)); do
		if [ $DRY_RUN -eq 1 ]; then
			log_info "[DRY-RUN] Would download $url to $out"
			return 0
		fi
		if curl -fsSL "$url" -o "$out"; then
			return 0
		fi
		sleep "$delay"
		delay=$(awk -v d="$delay" 'BEGIN{ printf "%.2f", d*2 }')
	done
	return 1
}

# Default to local installation
INSTALL_MODE="${1:-local}"
log_verbose "Selected mode: $INSTALL_MODE"

echo -e "${BLUE}=== Lintro Tool Installer ===${NC}"
echo -e "Mode: ${INSTALL_MODE}"
echo ""

# Determine installation paths based on mode
if [ "$INSTALL_MODE" = "--docker" ] || [ "$INSTALL_MODE" = "docker" ]; then
	BIN_DIR="/usr/local/bin"
	echo -e "${YELLOW}Installing tools system-wide for Docker environment${NC}"
else
	# Local installation - use ~/.local/bin
	BIN_DIR="$HOME/.local/bin"
	mkdir -p "$BIN_DIR"
	echo -e "${YELLOW}Installing tools locally to $BIN_DIR${NC}"
	echo -e "${YELLOW}Make sure $BIN_DIR is in your PATH${NC}"
fi

# Function to detect platform and architecture
detect_platform() {
	local os
	local arch
	os=$(uname -s)
	arch=$(uname -m)

	# Normalize OS names for hadolint
	case "$os" in
	Darwin) os="Darwin" ;;
	Linux) os="Linux" ;;
	MINGW* | MSYS* | CYGWIN*) os="Windows" ;;
	*) ;; # keep original value
	esac

	# Normalize architecture names for hadolint
	case "$arch" in
	x86_64) arch="x86_64" ;;
	amd64) arch="x86_64" ;;
	aarch64) arch="arm64" ;;
	arm64) arch="arm64" ;;
	*) ;; # keep original value
	esac

	echo "${os}-${arch}"
}

# Function to install Python package with fallbacks (uv pip preferred)
install_python_package() {
	local package="$1"
	local version="${2:-}"
	local full_package="$package"

	if [ -n "$version" ]; then
		full_package="$package==$version"
	fi

	# Prefer uv pip when available
	if command -v uv &>/dev/null; then
		if uv pip install "$full_package"; then
			# Copy the executable to target directory if it exists in uv environment
			local uv_path
			uv_path=$(uv run which "$package" 2>/dev/null || echo "")
			if [ -n "$uv_path" ] && [ -f "$uv_path" ]; then
				cp "$uv_path" "$BIN_DIR/$package"
				chmod +x "$BIN_DIR/$package"
				echo -e "${YELLOW}Copied $package from uv environment to $BIN_DIR${NC}"
			fi
			return 0
		fi
	fi

	# Fallback to pip
	if command -v pip &>/dev/null; then
		if pip install "$full_package"; then
			return 0
		fi
	fi

	# Try system package managers as last resort
	if command -v brew &>/dev/null; then
		if brew install "$package"; then
			return 0
		fi
	fi

	return 1
}

# Function to install a tool via curl with platform detection
install_tool_curl() {
	local tool_name="$1"
	local base_url="$2"
	local target_path="$BIN_DIR/$tool_name"

	echo -e "${BLUE}Installing $tool_name...${NC}"

	# Get platform info
	local platform
	platform=$(detect_platform)
	local download_url="${base_url}-${platform}"

	echo -e "${YELLOW}Detected platform: $platform${NC}"
	echo -e "${YELLOW}Download URL: $download_url${NC}"

	if download_with_retries "$download_url" "$target_path" 3; then
		chmod +x "$target_path"
		# Attempt checksum verification when available
		if [[ "$tool_name" == "hadolint" ]]; then
			local checksum_url="${download_url}.sha256"
			if download_with_retries "$checksum_url" "$target_path.sha256" 3; then
				echo -e "${BLUE}Verifying checksum for $tool_name...${NC}"
				# Portable verification regardless of filename in .sha256
				local expected
				expected=$(awk '{print $1}' "$target_path.sha256" | head -n1)
				local actual
				if command -v sha256sum >/dev/null 2>&1; then
					actual=$(sha256sum "$target_path" | awk '{print $1}')
				elif command -v shasum >/dev/null 2>&1; then
					actual=$(shasum -a 256 "$target_path" | awk '{print $1}')
				else
					echo -e "${YELLOW}⚠ No checksum tool available; skipping verification${NC}"
					actual=""
				fi
				if [[ -n "$actual" ]]; then
					if [[ "$expected" != "$actual" ]]; then
						echo -e "${RED}✗ Checksum mismatch for $tool_name${NC}"
						exit 1
					fi
					echo -e "${GREEN}✓ Checksum verified${NC}"
				fi
				rm -f "$target_path.sha256" || true
			fi
		fi
		echo -e "${GREEN}✓ $tool_name installed successfully${NC}"
	else
		echo -e "${YELLOW}Direct download failed, trying alternative methods...${NC}"

		# For hadolint, try alternative installation methods
		if [ "$tool_name" = "hadolint" ]; then
			# Try installing via package managers
			if command -v brew &>/dev/null; then
				echo -e "${YELLOW}Trying Homebrew installation...${NC}"
				if brew install hadolint; then
					# Copy from Homebrew location to target
					local brew_path
					brew_path="$(brew --prefix hadolint)/bin/hadolint"
					if [ -f "$brew_path" ]; then
						cp "$brew_path" "$target_path"
						chmod +x "$target_path"
						echo -e "${GREEN}✓ hadolint installed successfully via Homebrew${NC}"
						return 0
					fi
				fi
			fi

			# Remove invalid pip fallback for hadolint
		fi

		echo -e "${RED}✗ Failed to install $tool_name from $download_url and all fallback methods${NC}"
		exit 1
	fi
}

# Function to install system dependencies for Docker
install_system_deps() {
	if [ "$INSTALL_MODE" = "--docker" ] || [ "$INSTALL_MODE" = "docker" ]; then
		echo -e "${BLUE}Installing system dependencies...${NC}"

		# Update package lists
		if [ $DRY_RUN -eq 1 ]; then
			log_info "[DRY-RUN] Would run apt-get update and install system packages"
			return
		fi
		apt-get update

		# Install essential packages
		apt-get install -y --no-install-recommends \
			curl \
			ca-certificates \
			git \
			gnupg

		# Note: bun will be installed via ensure_bun_installed() when needed

		# Install Python packages via apt (more reliable in Docker)
		apt-get install -y --no-install-recommends \
			python3-pip \
			python3-venv

		# Clean up
		apt-get clean
		rm -rf /var/lib/apt/lists/*

		echo -e "${GREEN}✓ System dependencies installed${NC}"
	fi
}

# Main installation process
main() {
	echo -e "${YELLOW}Starting tool installation...${NC}"
	echo ""

	# Install system dependencies if in Docker mode
	if [ "$INSTALL_MODE" = "--docker" ] || [ "$INSTALL_MODE" = "docker" ]; then
		install_system_deps
	fi

	# Install hadolint (Docker linting)
	# hadolint with checksum verification when available
	HADOLINT_VERSION=$(get_tool_version "hadolint") || exit 1
	install_tool_curl "hadolint" \
		"https://github.com/hadolint/hadolint/releases/download/v${HADOLINT_VERSION}/hadolint"

	# Install gitleaks (secret detection)
	echo -e "${BLUE}Installing gitleaks...${NC}"
	GITLEAKS_VERSION=$(get_tool_version "gitleaks") || exit 1
	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install gitleaks v${GITLEAKS_VERSION}"
	elif command -v gitleaks &>/dev/null; then
		echo -e "${GREEN}✓ gitleaks already installed${NC}"
	else
		tmpdir=$(mktemp -d)
		os=$(uname -s | tr '[:upper:]' '[:lower:]')
		arch=$(uname -m)
		case "$arch" in
		x86_64 | amd64) arch_name="x64" ;;
		aarch64 | arm64) arch_name="arm64" ;;
		*) arch_name="x64" ;;
		esac
		tgz_url="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_${os}_${arch_name}.tar.gz"
		checksum_url="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_checksums.txt"
		if download_with_retries "$tgz_url" "$tmpdir/gitleaks.tar.gz" 3; then
			# Verify checksum if available
			if download_with_retries "$checksum_url" "$tmpdir/checksums.txt" 3; then
				echo -e "${BLUE}Verifying checksum for gitleaks...${NC}"
				expected=$(grep "gitleaks_${GITLEAKS_VERSION}_${os}_${arch_name}.tar.gz" "$tmpdir/checksums.txt" | awk '{print $1}')
				if [ -z "$expected" ]; then
					echo -e "${RED}✗ Checksum entry not found for gitleaks_${GITLEAKS_VERSION}_${os}_${arch_name}.tar.gz in ${tmpdir}/checksums.txt${NC}"
					rm -rf "$tmpdir"
					exit 1
				fi
				if command -v sha256sum >/dev/null 2>&1; then
					actual=$(sha256sum "$tmpdir/gitleaks.tar.gz" | awk '{print $1}')
				elif command -v shasum >/dev/null 2>&1; then
					actual=$(shasum -a 256 "$tmpdir/gitleaks.tar.gz" | awk '{print $1}')
				else
					echo -e "${RED}✗ Unable to compute checksum: no hash tool found (sha256sum or shasum required)${NC}"
					rm -rf "$tmpdir"
					exit 1
				fi
				if [ "$expected" != "$actual" ]; then
					echo -e "${RED}✗ Checksum mismatch for gitleaks (expected: $expected, got: $actual)${NC}"
					rm -rf "$tmpdir"
					exit 1
				fi
				echo -e "${GREEN}✓ Checksum verified${NC}"
			fi
			tar -xzf "$tmpdir/gitleaks.tar.gz" -C "$tmpdir"
			cp "$tmpdir/gitleaks" "$BIN_DIR/gitleaks"
			chmod +x "$BIN_DIR/gitleaks"
			echo -e "${GREEN}✓ gitleaks installed successfully${NC}"
		else
			echo -e "${RED}✗ Failed to download gitleaks${NC}"
			rm -rf "$tmpdir"
			exit 1
		fi
		rm -rf "$tmpdir"
	fi

	# Install actionlint (GitHub Actions workflow linter)
	# Prebuilt binaries: https://github.com/rhysd/actionlint/releases
	echo -e "${BLUE}Installing actionlint...${NC}"
	ACTIONLINT_VERSION="v$(get_tool_version "actionlint")" || exit 1
	# actionlint release assets are named actionlint_${version}_${os}_${arch}.tar.gz
	# We'll try to download and extract the binary
	tmpdir=$(mktemp -d)
	os=$(uname -s)
	arch=$(uname -m)
	case "$os" in
	Darwin) os_name="darwin" ;;
	Linux) os_name="linux" ;;
	*) os_name="linux" ;;
	esac
	case "$arch" in
	x86_64 | amd64) arch_name="amd64" ;;
	aarch64 | arm64) arch_name="arm64" ;;
	*) arch_name="amd64" ;;
	esac
	tgz_url="https://github.com/rhysd/actionlint/releases/download/${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION#v}_${os_name}_${arch_name}.tar.gz"
	if download_with_retries "$tgz_url" "$tmpdir/actionlint.tgz" 3; then
		# Verify SHA256 if checksum is available
		checksum_url="${tgz_url}.sha256"
		if download_with_retries "$checksum_url" "$tmpdir/actionlint.tgz.sha256" 3; then
			echo -e "${BLUE}Verifying checksum for actionlint...${NC}"
			if command -v sha256sum >/dev/null 2>&1; then
				if ! (cd "$tmpdir" && sha256sum -c actionlint.tgz.sha256 >/dev/null 2>&1); then
					echo -e "${RED}✗ Checksum mismatch for actionlint${NC}"
					exit 1
				fi
			elif command -v shasum >/dev/null 2>&1; then
				expected=$(cut -d' ' -f1 <"$tmpdir/actionlint.tgz.sha256")
				actual=$(shasum -a 256 "$tmpdir/actionlint.tgz" | awk '{print $1}')
				if [[ "$expected" != "$actual" ]]; then
					echo -e "${RED}✗ Checksum mismatch for actionlint${NC}"
					exit 1
				fi
			fi
		fi
		tar -xzf "$tmpdir/actionlint.tgz" -C "$tmpdir" >/dev/null 2>&1 || true
		if [ -f "$tmpdir/actionlint" ]; then
			cp "$tmpdir/actionlint" "$BIN_DIR/actionlint"
			chmod +x "$BIN_DIR/actionlint"
			echo -e "${GREEN}✓ actionlint installed successfully${NC}"
		else
			echo -e "${YELLOW}⚠ Could not find extracted actionlint binary${NC}"
		fi
	else
		echo -e "${YELLOW}⚠ Failed to download actionlint prebuilt binary${NC}"
	fi
	rm -rf "$tmpdir" || true

	# Install shfmt (shell script formatter)
	echo -e "${BLUE}Installing shfmt...${NC}"
	SHFMT_VERSION=$(get_tool_version "shfmt") || exit 1
	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install shfmt v${SHFMT_VERSION}"
	elif command -v shfmt &>/dev/null; then
		echo -e "${GREEN}✓ shfmt already installed${NC}"
	else
		os=$(uname -s | tr '[:upper:]' '[:lower:]')
		arch=$(uname -m)
		case "$arch" in
		x86_64 | amd64) arch="amd64" ;;
		aarch64 | arm64) arch="arm64" ;;
		esac
		binary_url="https://github.com/mvdan/sh/releases/download/v${SHFMT_VERSION}/shfmt_v${SHFMT_VERSION}_${os}_${arch}"
		if download_with_retries "$binary_url" "$BIN_DIR/shfmt" 3; then
			chmod +x "$BIN_DIR/shfmt"
			echo -e "${GREEN}✓ shfmt installed successfully${NC}"
		else
			echo -e "${RED}✗ Failed to download shfmt${NC}"
			exit 1
		fi
	fi

	# Install Rust toolchain, clippy, and rustfmt
	echo -e "${BLUE}Installing Rust toolchain, clippy, and rustfmt...${NC}"
	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install Rust toolchain, clippy, and rustfmt"
	elif command -v rustc &>/dev/null && cargo clippy --version &>/dev/null && rustfmt --version &>/dev/null; then
		echo -e "${GREEN}✓ Rust toolchain, clippy, and rustfmt already installed${NC}"
	else
		# Install rustup if not present
		if ! command -v rustup &>/dev/null; then
			echo -e "${YELLOW}Installing rustup...${NC}"
			curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable --component clippy --component rustfmt
			# Source cargo environment
			if [ -f "$HOME/.cargo/env" ]; then
				# SC1091: cargo env is created by rustup installer at runtime
				# shellcheck disable=SC1091
				source "$HOME/.cargo/env"
			fi
		else
			echo -e "${YELLOW}rustup already installed, updating toolchain...${NC}"
			rustup update stable
			rustup component add clippy
			rustup component add rustfmt
		fi

		# Verify installation
		if command -v rustc &>/dev/null && cargo clippy --version &>/dev/null && rustfmt --version &>/dev/null; then
			echo -e "${GREEN}✓ Rust toolchain, clippy, and rustfmt installed successfully${NC}"
		else
			echo -e "${RED}✗ Failed to install Rust toolchain, clippy, and rustfmt${NC}"
			exit 1
		fi
	fi

	# Install cargo-audit (Rust dependency vulnerability scanner)
	echo -e "${BLUE}Installing cargo-audit...${NC}"
	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install cargo-audit"
	elif command -v cargo-audit &>/dev/null; then
		echo -e "${GREEN}✓ cargo-audit already installed${NC}"
	elif command -v cargo &>/dev/null; then
		if cargo install cargo-audit --locked; then
			echo -e "${GREEN}✓ cargo-audit installed successfully${NC}"
		else
			echo -e "${YELLOW}⚠ Failed to install cargo-audit (optional tool)${NC}"
		fi
	else
		echo -e "${YELLOW}⚠ cargo not available, skipping cargo-audit${NC}"
	fi

	# Install ruff (Python linting and formatting)
	echo -e "${BLUE}Installing ruff...${NC}"
	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install ruff"
	elif install_python_package "ruff"; then
		echo -e "${GREEN}✓ ruff installed successfully${NC}"
	else
		if command -v brew &>/dev/null; then
			echo -e "${YELLOW}Trying Homebrew for ruff...${NC}"
			if [ $DRY_RUN -eq 1 ]; then
				log_info "[DRY-RUN] Would install ruff via brew"
			else
				brew install ruff || {
					echo -e "${RED}✗ Failed to install ruff via Homebrew${NC}"
					exit 1
				}
			fi
			echo -e "${GREEN}✓ ruff installed successfully via Homebrew${NC}"
		else
			echo -e "${RED}✗ Cannot install ruff automatically; please install via your package manager.${NC}"
			exit 1
		fi
	fi

	# Install black (Python code formatter)
	echo -e "${BLUE}Installing black...${NC}"
	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install black"
	elif install_python_package "black"; then
		echo -e "${GREEN}✓ black installed successfully${NC}"
	else
		echo -e "${RED}✗ Failed to install black${NC}"
		exit 1
	fi

	# Install bandit (Python security linter)
	echo -e "${BLUE}Installing bandit...${NC}"
	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install bandit==1.8.6"
	elif install_python_package "bandit" "1.8.6"; then
		echo -e "${GREEN}✓ bandit installed successfully${NC}"
	else
		echo -e "${RED}✗ Failed to install bandit${NC}"
		exit 1
	fi

	# Install mypy (Python type checker)
	echo -e "${BLUE}Installing mypy...${NC}"
	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install mypy"
	elif install_python_package "mypy"; then
		echo -e "${GREEN}✓ mypy installed successfully${NC}"
	else
		echo -e "${RED}✗ Failed to install mypy${NC}"
		exit 1
	fi

	# Install prettier via bun (JavaScript/JSON formatting)
	echo -e "${BLUE}Installing prettier...${NC}"

	# Ensure bun is available
	if ! ensure_bun_installed; then
		exit 1
	fi

	# Read prettier version from package.json if it exists
	# Check devDependencies first, then dependencies, then fall back to latest
	if [ -f "package.json" ]; then
		PRETTIER_VERSION=$(jq -r '.devDependencies.prettier // .dependencies.prettier // "latest"' package.json 2>/dev/null || echo "latest")
		# Strip caret prefix if present (e.g., "^3.7.3" -> "3.7.3")
		PRETTIER_VERSION="${PRETTIER_VERSION#^}"
	else
		PRETTIER_VERSION="latest"
	fi

	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install prettier@${PRETTIER_VERSION} globally via bun"
	elif bun add -g "prettier@${PRETTIER_VERSION}"; then
		echo -e "${GREEN}✓ prettier@${PRETTIER_VERSION} installed successfully${NC}"
	else
		echo -e "${RED}✗ Failed to install prettier${NC}"
		exit 1
	fi

	# Install markdownlint-cli2 via bun (Markdown linting)
	echo -e "${BLUE}Installing markdownlint-cli2...${NC}"

	# Ensure bun is available (should already be installed for prettier)
	if ! ensure_bun_installed; then
		exit 1
	fi

	# Read markdownlint-cli2 version from package.json if it exists
	# Check devDependencies first, then dependencies, then fall back to latest
	if [ -f "package.json" ]; then
		MARKDOWNLINT_VERSION=$(jq -r '.devDependencies."markdownlint-cli2" // .dependencies."markdownlint-cli2" // "latest"' package.json 2>/dev/null || echo "latest")
		# Strip caret prefix if present (e.g., "^0.17.2" -> "0.17.2")
		MARKDOWNLINT_VERSION="${MARKDOWNLINT_VERSION#^}"
	else
		MARKDOWNLINT_VERSION="latest"
	fi

	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install markdownlint-cli2@${MARKDOWNLINT_VERSION} globally via bun"
	elif bun add -g "markdownlint-cli2@${MARKDOWNLINT_VERSION}"; then
		echo -e "${GREEN}✓ markdownlint-cli2@${MARKDOWNLINT_VERSION} installed successfully${NC}"
	else
		echo -e "${RED}✗ Failed to install markdownlint-cli2${NC}"
		exit 1
	fi

	# Install semgrep (security scanner)
	echo -e "${BLUE}Installing semgrep...${NC}"
	SEMGREP_VERSION=$(get_tool_version "semgrep") || exit 1
	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install semgrep==${SEMGREP_VERSION}"
	elif install_python_package "semgrep" "$SEMGREP_VERSION"; then
		echo -e "${GREEN}✓ semgrep installed successfully${NC}"
	else
		echo -e "${RED}✗ Failed to install semgrep${NC}"
		exit 1
	fi

	# Install shellcheck (shell script linter)
	echo -e "${BLUE}Installing shellcheck...${NC}"
	SHELLCHECK_VERSION=$(get_tool_version "shellcheck") || exit 1

	# Helper function for shellcheck binary installation
	install_shellcheck_binary() {
		local tmpdir
		tmpdir=$(mktemp -d)
		local os arch tar_url
		os=$(uname -s | tr '[:upper:]' '[:lower:]')
		arch=$(uname -m)
		case "$arch" in
		x86_64 | amd64) arch="x86_64" ;;
		aarch64 | arm64) arch="aarch64" ;;
		esac
		tar_url="https://github.com/koalaman/shellcheck/releases/download/v${SHELLCHECK_VERSION}/shellcheck-v${SHELLCHECK_VERSION}.${os}.${arch}.tar.xz"
		if download_with_retries "$tar_url" "$tmpdir/shellcheck.tar.xz" 3; then
			tar -xJf "$tmpdir/shellcheck.tar.xz" -C "$tmpdir"
			cp "$tmpdir/shellcheck-v${SHELLCHECK_VERSION}/shellcheck" "$BIN_DIR/shellcheck"
			chmod +x "$BIN_DIR/shellcheck"
			rm -rf "$tmpdir"
			return 0
		else
			rm -rf "$tmpdir"
			return 1
		fi
	}

	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install shellcheck v${SHELLCHECK_VERSION}"
	elif command -v shellcheck &>/dev/null; then
		# Check if installed version meets minimum requirement
		installed_version=$(shellcheck --version 2>/dev/null | grep -oE 'version: [0-9]+\.[0-9]+\.[0-9]+' | cut -d' ' -f2)
		if [ -n "$installed_version" ]; then
			# Compare versions using portable version_ge function from utils.sh
			if version_ge "$installed_version" "$SHELLCHECK_VERSION"; then
				echo -e "${GREEN}✓ shellcheck v${installed_version} already installed (>= v${SHELLCHECK_VERSION})${NC}"
			else
				echo -e "${YELLOW}⚠ shellcheck v${installed_version} is older than required v${SHELLCHECK_VERSION}, upgrading...${NC}"
				if install_shellcheck_binary; then
					echo -e "${GREEN}✓ shellcheck upgraded to v${SHELLCHECK_VERSION}${NC}"
				else
					echo -e "${RED}✗ Failed to download shellcheck${NC}"
					exit 1
				fi
			fi
		else
			# Could not parse version, treat as not installed
			echo -e "${YELLOW}⚠ Could not determine shellcheck version, installing v${SHELLCHECK_VERSION}...${NC}"
			if install_shellcheck_binary; then
				echo -e "${GREEN}✓ shellcheck installed successfully${NC}"
			else
				echo -e "${RED}✗ Failed to download shellcheck${NC}"
				exit 1
			fi
		fi
	else
		if install_shellcheck_binary; then
			echo -e "${GREEN}✓ shellcheck installed successfully${NC}"
		else
			echo -e "${RED}✗ Failed to download shellcheck${NC}"
			exit 1
		fi
	fi

	# Install biome via bun (JavaScript/TypeScript linting and formatting)
	echo -e "${BLUE}Installing biome...${NC}"

	# Ensure bun is available (should already be installed for prettier)
	if ! ensure_bun_installed; then
		exit 1
	fi

	# Read biome version from package.json if it exists
	# Check devDependencies first, then dependencies, then fall back to latest
	if [ -f "package.json" ]; then
		BIOME_VERSION=$(jq -r '.devDependencies."@biomejs/biome" // .dependencies."@biomejs/biome" // "latest"' package.json 2>/dev/null || echo "latest")
		# Strip caret prefix if present (e.g., "^2.3.9" -> "2.3.9")
		BIOME_VERSION="${BIOME_VERSION#^}"
	else
		BIOME_VERSION="latest"
	fi

	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install @biomejs/biome@${BIOME_VERSION} globally via bun"
	elif bun add -g "@biomejs/biome@${BIOME_VERSION}"; then
		echo -e "${GREEN}✓ @biomejs/biome@${BIOME_VERSION} installed successfully${NC}"
	else
		echo -e "${RED}✗ Failed to install biome${NC}"
		exit 1
	fi

	# Install yamllint (Python package)
	echo -e "${BLUE}Installing yamllint...${NC}"
	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install yamllint"
	elif install_python_package "yamllint"; then
		echo -e "${GREEN}✓ yamllint installed successfully${NC}"
	else
		echo -e "${RED}✗ Failed to install yamllint${NC}"
		exit 1
	fi

	# Install pydoclint (Python docstring linter)
	echo -e "${BLUE}Installing pydoclint...${NC}"

	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install pydoclint"
	elif install_python_package "pydoclint"; then
		echo -e "${GREEN}✓ pydoclint installed successfully${NC}"
	else
		echo -e "${RED}✗ Failed to install pydoclint${NC}"
		exit 1
	fi

	# Install sqlfluff (SQL linter and formatter)
	echo -e "${BLUE}Installing sqlfluff...${NC}"
	SQLFLUFF_VERSION=$(get_tool_version "sqlfluff") || exit 1
	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install sqlfluff==${SQLFLUFF_VERSION}"
	elif install_python_package "sqlfluff" "$SQLFLUFF_VERSION"; then
		echo -e "${GREEN}✓ sqlfluff installed successfully${NC}"
	else
		echo -e "${RED}✗ Failed to install sqlfluff${NC}"
		exit 1
	fi

	# Install taplo (TOML linter and formatter)
	echo -e "${BLUE}Installing taplo...${NC}"
	TAPLO_VERSION=$(get_tool_version "taplo") || exit 1
	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install taplo v${TAPLO_VERSION}"
	elif command -v taplo &>/dev/null; then
		echo -e "${GREEN}✓ taplo already installed${NC}"
	else
		taplo_installed=false
		tmpdir=$(mktemp -d)
		os=$(uname -s | tr '[:upper:]' '[:lower:]')
		arch=$(uname -m)
		case "$arch" in
		x86_64 | amd64) arch="x86_64" ;;
		aarch64 | arm64) arch="aarch64" ;;
		esac
		# taplo releases use format: taplo-full-{os}-{arch}.gz
		gz_url="https://github.com/tamasfe/taplo/releases/download/${TAPLO_VERSION}/taplo-full-${os}-${arch}.gz"
		# Check if GitHub release exists before attempting download
		if curl -sfIL "$gz_url" >/dev/null 2>&1; then
			if download_with_retries "$gz_url" "$tmpdir/taplo.gz" 3; then
				# Verify checksum BEFORE installing binary
				checksum_url="${gz_url}.sha256"
				checksum_ok=true
				if download_with_retries "$checksum_url" "$tmpdir/taplo.gz.sha256" 3; then
					echo -e "${BLUE}Verifying checksum for taplo...${NC}"
					expected=$(awk '{print $1}' "$tmpdir/taplo.gz.sha256" | head -n1)
					if command -v sha256sum >/dev/null 2>&1; then
						actual=$(sha256sum "$tmpdir/taplo.gz" | awk '{print $1}')
					elif command -v shasum >/dev/null 2>&1; then
						actual=$(shasum -a 256 "$tmpdir/taplo.gz" | awk '{print $1}')
					else
						echo -e "${YELLOW}⚠ No sha256 tool available, skipping checksum verification${NC}"
						actual="$expected"
					fi
					if [ "$expected" = "$actual" ]; then
						echo -e "${GREEN}✓ Checksum verified${NC}"
					else
						echo -e "${RED}✗ Checksum mismatch for taplo (expected: $expected, got: $actual)${NC}"
						checksum_ok=false
					fi
					rm -f "$tmpdir/taplo.gz.sha256" || true
				fi
				# Only install if checksum passed (or wasn't available)
				if [ "$checksum_ok" = true ]; then
					gunzip -c "$tmpdir/taplo.gz" >"$BIN_DIR/taplo"
					chmod +x "$BIN_DIR/taplo"
					echo -e "${GREEN}✓ taplo installed successfully${NC}"
					taplo_installed=true
				fi
			fi
		else
			echo -e "${YELLOW}⚠ GitHub release for taplo v${TAPLO_VERSION} not available${NC}"
		fi
		rm -rf "$tmpdir"

		# Fallback to cargo if binary download failed
		if [ "$taplo_installed" = false ]; then
			echo -e "${BLUE}Attempting fallback installation via cargo...${NC}"
			if command -v cargo &>/dev/null; then
				echo -e "${BLUE}Installing taplo via cargo...${NC}"
				if cargo install taplo-cli --locked; then
					# Derive cargo bin directory from CARGO_HOME or default
					cargo_bin="${CARGO_HOME:-$HOME/.cargo}/bin"
					# Check for executable taplo in cargo bin, fall back to PATH
					if [ -x "$cargo_bin/taplo" ]; then
						cp "$cargo_bin/taplo" "$BIN_DIR/taplo"
						chmod +x "$BIN_DIR/taplo"
						echo -e "${GREEN}✓ taplo installed via cargo${NC}"
						taplo_installed=true
					elif command -v taplo &>/dev/null; then
						echo -e "${GREEN}✓ taplo installed via cargo (found on PATH)${NC}"
						taplo_installed=true
					fi
				fi
			fi
		fi

		if [ "$taplo_installed" = false ]; then
			echo -e "${RED}✗ Failed to install taplo${NC}"
			exit 1
		fi
	fi

	# Install typescript via bun (TypeScript compiler)
	echo -e "${BLUE}Installing typescript...${NC}"

	if ! ensure_bun_installed; then
		exit 1
	fi

	TYPESCRIPT_VERSION=$(get_tool_version "typescript") || exit 1
	if [ $DRY_RUN -eq 1 ]; then
		log_info "[DRY-RUN] Would install typescript@${TYPESCRIPT_VERSION} globally via bun"
	elif bun add -g "typescript@${TYPESCRIPT_VERSION}"; then
		echo -e "${GREEN}✓ typescript@${TYPESCRIPT_VERSION} installed successfully${NC}"
	else
		echo -e "${RED}✗ Failed to install typescript${NC}"
		exit 1
	fi

	echo ""
	echo -e "${GREEN}=== Installation Complete! ===${NC}"
	echo ""
	echo -e "${YELLOW}Installed tools:${NC}"
	echo "  - actionlint (GitHub Actions linting)"
	echo "  - bandit (Python security checks)"
	echo "  - biome (JavaScript/TypeScript linting and formatting)"
	echo "  - black (Python formatting)"
	echo "  - cargo-audit (Rust dependency vulnerability scanning)"
	echo "  - clippy (Rust linting)"
	echo "  - rustfmt (Rust formatting)"
	echo "  - pydoclint (Python docstring validation)"
	echo "  - gitleaks (Secret detection)"
	echo "  - hadolint (Docker linting)"
	echo "  - markdownlint-cli2 (Markdown linting)"
	echo "  - prettier (JavaScript/JSON formatting)"
	echo "  - ruff (Python linting and formatting)"
	echo "  - semgrep (Security scanning)"
	echo "  - shellcheck (Shell script linting)"
	echo "  - shfmt (Shell script formatting)"
	echo "  - sqlfluff (SQL linting and formatting)"
	echo "  - taplo (TOML linting and formatting)"
	echo "  - tsc (TypeScript type checking)"
	echo "  - mypy (Python type checking)"
	echo "  - yamllint (YAML linting)"
	echo ""

	# Verify installations
	echo -e "${YELLOW}Verifying installations...${NC}"

	tools_to_verify=("actionlint" "bandit" "biome" "black" "cargo-audit" "clippy" "rustfmt" "pydoclint" "gitleaks" "hadolint" "markdownlint-cli2" "prettier" "ruff" "semgrep" "shellcheck" "shfmt" "sqlfluff" "taplo" "tsc" "yamllint" "mypy")
	for tool in "${tools_to_verify[@]}"; do
		if [ "$tool" = "clippy" ]; then
			# Clippy is invoked through cargo
			if command -v cargo &>/dev/null && cargo clippy --version &>/dev/null; then
				version=$(cargo clippy --version 2>/dev/null || echo "installed")
				echo -e "${GREEN}✓ clippy: $version${NC}"
			else
				echo -e "${RED}✗ clippy: not found (requires cargo)${NC}"
			fi
		elif [ "$tool" = "rustfmt" ]; then
			# Rustfmt is a rustup component
			if command -v rustfmt &>/dev/null; then
				version=$(rustfmt --version 2>/dev/null || echo "installed")
				echo -e "${GREEN}✓ rustfmt: $version${NC}"
			else
				echo -e "${RED}✗ rustfmt: not found (requires rustup component add rustfmt)${NC}"
			fi
		elif command -v "$tool" &>/dev/null; then
			version=$("$tool" --version 2>/dev/null || echo "installed")
			echo -e "${GREEN}✓ $tool: $version${NC}"
		else
			echo -e "${RED}✗ $tool: not found in PATH${NC}"
		fi
	done

	if [ "$INSTALL_MODE" != "--docker" ] && [ "$INSTALL_MODE" != "docker" ]; then
		echo ""
		echo -e "${YELLOW}Local installation notes:${NC}"
		echo "  - Make sure $BIN_DIR is in your PATH"
		echo "  - Run 'uv sync --dev' to install Python dependencies"
		echo "  - Use './scripts/local/local-lintro.sh' or 'uv run lintro' to run lintro"
	fi
}

# Run main function
main "$@"
