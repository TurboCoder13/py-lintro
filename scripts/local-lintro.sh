#!/bin/bash
set -e

# local-lintro.sh - Enhanced local lintro runner
# 
# This script handles the complete setup and execution of lintro locally.
# It automatically installs missing tools and sets up the environment.

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Lintro Local Runner ===${NC}"

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo -e "${YELLOW}Loading environment variables from .env file...${NC}"
    export $(grep -v '^#' .env | xargs)
fi

# Function to check if tools are installed
check_and_install_tools() {
    echo -e "${BLUE}Checking tool availability...${NC}"
    
    # Check for required tools
    local missing_tools=()
    
    # Check system tools
    if ! command -v hadolint &> /dev/null; then
        missing_tools+=("hadolint")
    fi
    
    if ! command -v prettier &> /dev/null; then
        missing_tools+=("prettier")
    fi
    
    if ! command -v ruff &> /dev/null; then
        missing_tools+=("ruff")
    fi
    
    if ! command -v uv &> /dev/null; then
        missing_tools+=("uv")
    fi
    
    # If tools are missing, offer to install them
    if [ ${#missing_tools[@]} -gt 0 ]; then
        echo -e "${YELLOW}Missing tools: ${missing_tools[*]}${NC}"
        echo -e "${YELLOW}Would you like to install them automatically? (y/n)${NC}"
        read -r response
        
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}Installing missing tools...${NC}"
            if [ -f "./scripts/install-tools.sh" ]; then
                ./scripts/install-tools.sh --local
            else
                echo -e "${RED}Error: scripts/install-tools.sh not found${NC}"
                echo -e "${YELLOW}Please run the installation script manually or ensure tools are installed${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}Continuing without installing tools. Some lintro features may not work.${NC}"
        fi
    else
        echo -e "${GREEN}✓ All tools are available${NC}"
    fi
}

# Function to setup Python environment
setup_python_env() {
    echo -e "${BLUE}Setting up Python environment...${NC}"
    
    # Check if we're running in Docker (environment should be ready)
    if [ -n "$RUNNING_IN_DOCKER" ] || [ -f "/.dockerenv" ]; then
        echo -e "${GREEN}✓ Running in Docker - environment already set up${NC}"
        # In Docker, we don't need to create a virtual environment
        # The dependencies are already installed in the container
        return 0
    fi
    
    echo -e "${YELLOW}Setting up Python environment with uv...${NC}"
    
    # Ensure uv is available
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}Error: uv is required but not installed${NC}"
        echo -e "${YELLOW}Please install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
        exit 1
    fi
    
    # Sync Python dependencies including dev dependencies
    if ! uv sync --dev; then
        echo -e "${RED}Error: Failed to sync Python environment${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Python environment ready${NC}"
}

# Function to run lintro with enhanced error handling
run_lintro() {
    echo -e "${BLUE}Running lintro with arguments: $*${NC}"
    
    # Add some helpful defaults if no arguments provided
    if [ $# -eq 0 ]; then
        echo -e "${YELLOW}No arguments provided. Running 'lintro --help'${NC}"
        set -- "--help"
    fi
    
    # Run lintro with the provided arguments
    # In Docker, use uv run to execute within the container's virtual environment
    if [ -n "$RUNNING_IN_DOCKER" ] || [ -f "/.dockerenv" ]; then
        uv run lintro "$@"
        local exit_code=$?
        if [ $exit_code -eq 0 ]; then
            echo -e "${GREEN}✓ Lintro completed successfully${NC}"
        else
            echo -e "${RED}✗ Lintro exited with code $exit_code${NC}"
        fi
        exit $exit_code
    else
        if uv run lintro "$@"; then
            echo -e "${GREEN}✓ Lintro completed successfully${NC}"
        else
            local exit_code=$?
            echo -e "${RED}✗ Lintro exited with code $exit_code${NC}"
            
            # Provide helpful suggestions based on common issues
            if [ $exit_code -eq 127 ]; then
                echo -e "${YELLOW}Tip: Command not found. Check if lintro is properly installed.${NC}"
            elif [ $exit_code -eq 1 ]; then
                echo -e "${YELLOW}Tip: Lintro found issues. Use 'fmt' command to auto-fix where possible.${NC}"
            fi
            
            exit $exit_code
        fi
    fi
}

# Main execution flow
main() {
    # Check and install tools if needed (only if --install flag is provided)
    if [ "$1" = "--install" ] || [ "$1" = "-i" ]; then
        check_and_install_tools
        shift # Remove the --install flag from arguments
    fi
    
    # Setup Python environment
    setup_python_env
    
    # Run lintro
    run_lintro "$@"
}

# Show usage if --help is requested directly for this script
if [ "$1" = "--help" ] && [ "$2" = "script" ]; then
    echo "Usage: $0 [--install|-i] [lintro arguments...]"
    echo ""
    echo "Options:"
    echo "  --install, -i    Install missing tools before running lintro"
    echo ""
    echo "Examples:"
    echo "  $0 check --format grid"
    echo "  $0 --install fmt --tools prettier"
    echo "  $0 list-tools"
    echo ""
    echo "This script automatically sets up the Python environment and runs lintro."
    echo "Use --install to automatically install missing external tools."
    exit 0
fi

# Run main function with all arguments
main "$@" 