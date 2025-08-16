#!/usr/bin/env bash
set -euo pipefail

# install-tools.sh - Simplified tool installer for lintro
# 
# This script installs all external tools required by lintro.
# It uses consistent installation methods and is optimized for Docker environments.
#
# Usage:
#   ./scripts/install-tools.sh [--local|--docker]

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [--help] [--local|--docker]"
    echo ""
    echo "Tool Installation Script"
    echo "Installs all required linting and formatting tools."
    echo ""
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --local        Install tools locally (default)"
    echo "  --docker       Install tools system-wide for Docker"
    echo ""
    echo "This script installs:"
    echo "  - Ruff (Python linter and formatter)"
    echo "  - Darglint (docstring linter)"
    echo "  - Prettier (code formatter)"
    echo "  - Yamllint (YAML linter)"
    echo "  - Hadolint (Dockerfile linter)"
    echo ""
    echo "Use this script to set up a complete development environment."
    exit 0
fi

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default to local installation
INSTALL_MODE="${1:-local}"

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
    
    if curl -fsSL "$download_url" -o "$target_path"; then
        chmod +x "$target_path"
        # Attempt checksum verification when available
        if [[ "$tool_name" == "hadolint" ]]; then
            local checksum_url="${download_url}.sha256"
            if curl -fsSL "$checksum_url" -o "$target_path.sha256" 2>/dev/null; then
                echo -e "${BLUE}Verifying checksum for $tool_name...${NC}"
                if command -v sha256sum >/dev/null 2>&1; then
                    if sha256sum -c "$target_path.sha256" >/dev/null 2>&1; then
                        echo -e "${GREEN}✓ Checksum verified${NC}"
                    else
                        echo -e "${YELLOW}⚠ Checksum mismatch for $tool_name (continuing)${NC}"
                    fi
                elif command -v shasum >/dev/null 2>&1; then
                    local expected
                    expected=$(cut -d' ' -f1 < "$target_path.sha256")
                    local actual
                    actual=$(shasum -a 256 "$target_path" | awk '{print $1}')
                    if [[ "$expected" == "$actual" ]]; then
                        echo -e "${GREEN}✓ Checksum verified${NC}"
                    else
                        echo -e "${YELLOW}⚠ Checksum mismatch for $tool_name (continuing)${NC}"
                    fi
                else
                    echo -e "${YELLOW}⚠ No checksum tool available; skipping verification${NC}"
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
        apt-get update
        
        # Install essential packages
        apt-get install -y --no-install-recommends \
            curl \
            ca-certificates \
            git \
            gnupg
        
        # Install Node.js 20.x
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
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
    install_tool_curl "hadolint" \
        "https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint"
    
    # Install ruff (Python linting and formatting)
    echo -e "${BLUE}Installing ruff...${NC}"
    
    # Try the official installer first
    if curl -LsSf https://astral.sh/ruff/install.sh | sh; then
        # Copy ruff to the target directory if it was installed to ~/.local/bin
        if [ -f "$HOME/.local/bin/ruff" ] && [ "$HOME/.local/bin/ruff" != "$BIN_DIR/ruff" ]; then
            cp "$HOME/.local/bin/ruff" "$BIN_DIR/ruff"
            chmod +x "$BIN_DIR/ruff"
        fi
        echo -e "${GREEN}✓ ruff installed successfully${NC}"
    else
        echo -e "${YELLOW}Ruff installer failed, trying alternative method...${NC}"
        # Fallback: try installing via pip if available
        if command -v pip &> /dev/null; then
            if pip install ruff; then
                echo -e "${GREEN}✓ ruff installed successfully via pip${NC}"
            else
                echo -e "${RED}✗ Failed to install ruff via pip${NC}"
                exit 1
            fi
        else
            echo -e "${RED}✗ Failed to install ruff (no pip available)${NC}"
            exit 1
        fi
    fi
    
    # Install prettier via npm (JavaScript/JSON formatting)
    echo -e "${BLUE}Installing prettier...${NC}"
    
    # Check if npm is available
    if ! command -v npm &> /dev/null; then
        echo -e "${YELLOW}npm not found, trying to install Node.js...${NC}"
        
        # Try to install Node.js based on platform
        if command -v apt-get &> /dev/null && [ "$(id -u)" = "0" ]; then
            # Debian/Ubuntu with root privileges
            curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
            apt-get install -y --no-install-recommends nodejs
        elif command -v brew &> /dev/null; then
            # macOS with Homebrew
            brew install node
        elif command -v yum &> /dev/null && [ "$(id -u)" = "0" ]; then
            # RHEL/CentOS with root privileges
            curl -fsSL https://rpm.nodesource.com/setup_20.x | bash -
            yum install -y nodejs
        else
            echo -e "${RED}✗ Cannot install Node.js automatically. Please install Node.js manually.${NC}"
            exit 1
        fi
    fi
    
    if npm install -g prettier@3.6.0; then
        echo -e "${GREEN}✓ prettier installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install prettier${NC}"
        exit 1
    fi
    
    # Install yamllint (Python package)
    echo -e "${BLUE}Installing yamllint...${NC}"
    
    # Function to install Python package with fallbacks
    install_python_package() {
        local package="$1"
        local version="${2:-}"
        local full_package="$package"
        
        if [ -n "$version" ]; then
            full_package="$package==$version"
        fi
        
        # Try different installation methods in order of preference
        if [ -n "${GITHUB_ACTIONS:-}" ]; then
            # GitHub Actions - use pip directly
            if pip install "$full_package"; then
                return 0
            fi
        elif command -v uv &> /dev/null; then
            # Local uv environment - try uv pip first
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
    
    if install_python_package "yamllint"; then
        echo -e "${GREEN}✓ yamllint installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install yamllint${NC}"
        exit 1
    fi
    
    # Install darglint (Python package)
    echo -e "${BLUE}Installing darglint...${NC}"
    
    if install_python_package "darglint" "1.8.1"; then
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
    
    tools_to_verify=("hadolint" "prettier" "ruff" "yamllint" "darglint")
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