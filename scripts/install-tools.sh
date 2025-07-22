#!/bin/bash
set -e

# install-tools.sh - Simplified tool installer for lintro
# 
# This script installs all external tools required by lintro.
# It uses consistent installation methods and is optimized for Docker environments.
#
# Usage:
#   ./scripts/install-tools.sh [--local|--docker]

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

# Function to install a tool via curl
install_tool_curl() {
    local tool_name="$1"
    local download_url="$2"
    local target_path="$BIN_DIR/$tool_name"
    
    echo -e "${BLUE}Installing $tool_name...${NC}"
    
    if curl -fsSL "$download_url" -o "$target_path"; then
        chmod +x "$target_path"
        echo -e "${GREEN}✓ $tool_name installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install $tool_name${NC}"
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
            gnupg \
            software-properties-common
        
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
        "https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64"
    
    # Install ruff (Python linting and formatting)
    echo -e "${BLUE}Installing ruff...${NC}"
    if curl -LsSf https://astral.sh/ruff/install.sh | sh; then
        # Copy ruff to the target directory if it was installed to ~/.local/bin
        if [ -f "$HOME/.local/bin/ruff" ] && [ "$HOME/.local/bin/ruff" != "$BIN_DIR/ruff" ]; then
            cp "$HOME/.local/bin/ruff" "$BIN_DIR/ruff"
            chmod +x "$BIN_DIR/ruff"
        fi
        echo -e "${GREEN}✓ ruff installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install ruff${NC}"
        exit 1
    fi
    
    # Install prettier via npm (JavaScript/JSON formatting)
    echo -e "${BLUE}Installing prettier...${NC}"
    if npm install -g prettier@3.6.0; then
        echo -e "${GREEN}✓ prettier installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install prettier${NC}"
        exit 1
    fi
    
    # Install yamllint (platform-specific)
    echo -e "${BLUE}Installing yamllint...${NC}"
    
    # Check if we're in a GitHub Actions environment (no sudo privileges)
    if [ -n "$GITHUB_ACTIONS" ]; then
        # GitHub Actions - use pip
        if pip install yamllint; then
            echo -e "${GREEN}✓ yamllint installed successfully${NC}"
        else
            echo -e "${RED}✗ Failed to install yamllint${NC}"
            exit 1
        fi
    elif command -v apt-get &> /dev/null && [ "$(id -u)" = "0" ]; then
        # Linux with apt-get and root privileges - use pip for consistency
        if pip install yamllint; then
            echo -e "${GREEN}✓ yamllint installed successfully${NC}"
        else
            echo -e "${RED}✗ Failed to install yamllint${NC}"
            exit 1
        fi
    elif command -v brew &> /dev/null; then
        # macOS with Homebrew
        if brew install yamllint; then
            echo -e "${GREEN}✓ yamllint installed successfully${NC}"
        else
            echo -e "${RED}✗ Failed to install yamllint${NC}"
            exit 1
        fi
    else
        # Fallback to pip
        if pip install yamllint; then
            echo -e "${GREEN}✓ yamllint installed successfully${NC}"
        else
            echo -e "${RED}✗ Failed to install yamllint${NC}"
            exit 1
        fi
    fi
    
    # Install darglint via pip (Python package)
    echo -e "${BLUE}Installing darglint...${NC}"
    if pip install darglint==1.8.1; then
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
        echo "  - Use './scripts/local-lintro.sh' or 'uv run lintro' to run lintro"
    fi
}

# Run main function
main "$@" 