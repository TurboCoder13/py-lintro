#!/usr/bin/env bash
set -euo pipefail

# install-tools.sh - Simplified tool installer for lintro
# 
# This script installs all external tools required by lintro.
# It uses consistent installation methods and is optimized for Docker environments.
#
# Usage:
#   ./scripts/install-tools.sh [--help] [--dry-run] [--verbose] [--local|--docker]

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo "Usage: $0 [--help] [--dry-run] [--verbose] [--local|--docker]"
    echo ""
    echo "Tool Installation Script"
    echo "Installs all required linting and formatting tools."
    echo ""
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --dry-run      Show what would be done without executing"
    echo "  --verbose      Enable verbose output"
    echo "  --local        Install tools locally (default)"
    echo "  --docker       Install tools system-wide for Docker"
    echo ""
    echo "This script installs:"
    echo "  - Ruff (Python linter and formatter)"
    echo "  - Darglint (docstring linter)"
    echo "  - Black (Python formatter; runs as a post-check in Lintro)"
    echo "  - Prettier (code formatter)"
    echo "  - Yamllint (YAML linter)"
    echo "  - Hadolint (Dockerfile linter)"
    echo "  - Actionlint (GitHub Actions workflow linter)"
    echo "  - Bandit (Python security linter)"
    echo ""
    echo "Use this script to set up a complete development environment."
    exit 0
fi

# Global flags
DRY_RUN=0
VERBOSE=0

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
        --help|-h)
            # Already handled above
            shift
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done
set -- "${POSITIONAL[@]}"

# Logging helpers
log_info() { echo "[install-tools] $*"; }
log_verbose() { [ $VERBOSE -eq 1 ] && echo "[install-tools] [verbose] $*" || true; }

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Simple downloader with retries/backoff
download_with_retries() {
    local url="$1"; shift
    local out="$1"; shift
    local attempts=${1:-3}
    local delay=0.5
    local i
    for ((i=1; i<=attempts; i++)); do
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
    local os=$(uname -s)
    local arch=$(uname -m)
    
    # Normalize OS names for hadolint
    case "$os" in
        Darwin) os="Darwin" ;;
        Linux) os="Linux" ;;
        MINGW*|MSYS*|CYGWIN*) os="Windows" ;;
        *) os="$os" ;;
    esac
    
    # Normalize architecture names for hadolint
    case "$arch" in
        x86_64) arch="x86_64" ;;
        amd64) arch="x86_64" ;;
        aarch64) arch="arm64" ;;
        arm64) arch="arm64" ;;
        *) arch="$arch" ;;
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
    if command -v uv &> /dev/null; then
        if uv pip install "$full_package"; then
            # Copy the executable to target directory if it exists in uv environment
            local uv_path=$(uv run which "$package" 2>/dev/null || echo "")
            if [ -n "$uv_path" ] && [ -f "$uv_path" ]; then
                cp "$uv_path" "$BIN_DIR/$package"
                chmod +x "$BIN_DIR/$package"
                echo -e "${YELLOW}Copied $package from uv environment to $BIN_DIR${NC}"
            fi
            return 0
        fi
    fi

    # Fallback to pip
    if command -v pip &> /dev/null; then
        if pip install "$full_package"; then
            return 0
        fi
    fi

    # Try system package managers as last resort
    if command -v brew &> /dev/null; then
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
    local platform=$(detect_platform)
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
            if command -v brew &> /dev/null; then
                echo -e "${YELLOW}Trying Homebrew installation...${NC}"
                if brew install hadolint; then
                    # Copy from Homebrew location to target
                    local brew_path=$(brew --prefix hadolint)/bin/hadolint
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
        
        # Install Node.js/npm from distribution repositories (no curl|bash)
        apt-get install -y --no-install-recommends nodejs npm || \
            apt-get install -y --no-install-recommends nodejs
        
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
    install_tool_curl "hadolint" \
        "https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint"

    # Install actionlint (GitHub Actions workflow linter)
    # Prebuilt binaries: https://github.com/rhysd/actionlint/releases
    echo -e "${BLUE}Installing actionlint...${NC}"
    ACTIONLINT_VERSION="v1.7.7"
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
        x86_64|amd64) arch_name="amd64" ;;
        aarch64|arm64) arch_name="arm64" ;;
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
                expected=$(cut -d' ' -f1 < "$tmpdir/actionlint.tgz.sha256")
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
    
    # Install ruff (Python linting and formatting)
    echo -e "${BLUE}Installing ruff...${NC}"
    if [ $DRY_RUN -eq 1 ]; then
        log_info "[DRY-RUN] Would install ruff"
    elif install_python_package "ruff"; then
        echo -e "${GREEN}✓ ruff installed successfully${NC}"
    else
        if command -v brew &> /dev/null; then
            echo -e "${YELLOW}Trying Homebrew for ruff...${NC}"
            if [ $DRY_RUN -eq 1 ]; then
                log_info "[DRY-RUN] Would install ruff via brew"
            else
                brew install ruff || {
                    echo -e "${RED}✗ Failed to install ruff via Homebrew${NC}"; exit 1;
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

    # Install prettier via npm (JavaScript/JSON formatting)
    echo -e "${BLUE}Installing prettier...${NC}"
    
    # Check if npm is available
    if ! command -v npm &> /dev/null; then
        echo -e "${YELLOW}npm not found, trying to install Node.js...${NC}"
        
        # Try to install Node.js based on platform
        if command -v apt-get &> /dev/null && [ "$(id -u)" = "0" ]; then
            # Debian/Ubuntu with root privileges (no curl|bash installers)
            if [ $DRY_RUN -eq 1 ]; then
                log_info "[DRY-RUN] Would install nodejs/npm via apt-get"
            else
                apt-get update
                apt-get install -y --no-install-recommends nodejs npm || \
                apt-get install -y --no-install-recommends nodejs
            fi
        elif command -v brew &> /dev/null; then
            # macOS with Homebrew
            if [ $DRY_RUN -eq 1 ]; then
                log_info "[DRY-RUN] Would install node via brew"
            else
                brew install node
            fi
        elif command -v yum &> /dev/null && [ "$(id -u)" = "0" ]; then
            # RHEL/CentOS with root privileges (no curl|bash installers)
            if [ $DRY_RUN -eq 1 ]; then
                log_info "[DRY-RUN] Would install nodejs/npm via yum"
            else
                yum install -y nodejs npm || yum install -y nodejs
            fi
        else
            echo -e "${RED}✗ Cannot install Node.js automatically. Please install Node.js manually.${NC}"
            exit 1
        fi
    fi
    
    if [ $DRY_RUN -eq 1 ]; then
        log_info "[DRY-RUN] Would install prettier@3.6.0 globally via npm"
    elif npm install -g prettier@3.6.0; then
        echo -e "${GREEN}✓ prettier installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install prettier${NC}"
        exit 1
    fi
    
    # Install yamllint (Python package)
    echo -e "${BLUE}Installing yamllint...${NC}"
    
    # Function to install Python package with fallbacks (uv pip preferred)
    install_python_package() {
        local package="$1"
        local version="${2:-}"
        local full_package="$package"
        
        if [ -n "$version" ]; then
            full_package="$package==$version"
        fi
        
        # Prefer uv pip when available
        if command -v uv &> /dev/null; then
            if uv pip install "$full_package"; then
                # Copy the executable to target directory if it exists in uv environment
                local uv_path=$(uv run which "$package" 2>/dev/null || echo "")
                if [ -n "$uv_path" ] && [ -f "$uv_path" ]; then
                    cp "$uv_path" "$BIN_DIR/$package"
                    chmod +x "$BIN_DIR/$package"
                    echo -e "${YELLOW}Copied $package from uv environment to $BIN_DIR${NC}"
                fi
                return 0
            fi
        fi
        
        # Fallback to pip
        if command -v pip &> /dev/null; then
            if pip install "$full_package"; then
                return 0
            fi
        fi
        
        # Try system package managers as last resort
        if command -v brew &> /dev/null; then
            if brew install "$package"; then
                return 0
            fi
        fi
        
        return 1
    }
    
    if [ $DRY_RUN -eq 1 ]; then
        log_info "[DRY-RUN] Would install yamllint"
    elif install_python_package "yamllint"; then
        echo -e "${GREEN}✓ yamllint installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install yamllint${NC}"
        exit 1
    fi
    
    # Install darglint (Python package)
    echo -e "${BLUE}Installing darglint...${NC}"
    
    if [ $DRY_RUN -eq 1 ]; then
        log_info "[DRY-RUN] Would install darglint==1.8.1"
    elif install_python_package "darglint" "1.8.1"; then
        echo -e "${GREEN}✓ darglint installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install darglint${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}=== Installation Complete! ===${NC}"
    echo ""
    echo -e "${YELLOW}Installed tools:${NC}"
    echo "  - hadolint (Docker linting)"
    echo "  - prettier (JavaScript/JSON formatting)"
    echo "  - ruff (Python linting and formatting)"
    echo "  - yamllint (YAML linting)"
    echo "  - darglint (Python docstring validation)"
    echo ""
    
    # Verify installations
    echo -e "${YELLOW}Verifying installations...${NC}"
    
    tools_to_verify=("hadolint" "actionlint" "prettier" "ruff" "bandit" "yamllint" "darglint")
    for tool in "${tools_to_verify[@]}"; do
        if command -v "$tool" &> /dev/null; then
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