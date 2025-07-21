#!/bin/bash

# Exit on any error
set -e

# local-test.sh - Enhanced local test runner
# 
# This script handles the complete setup and execution of tests locally.
# It automatically checks tool availability and runs appropriate tests.

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
VERBOSE=0
TEST_FILES=()

# Function to setup Python environment
setup_python_env() {
    echo -e "${BLUE}Setting up Python environment...${NC}"
    
    # Check if we're running in Docker
    if [ -n "$RUNNING_IN_DOCKER" ]; then
        echo -e "${YELLOW}Running in Docker environment${NC}"
        # In Docker, the environment is already set up by the Dockerfile
        # Just ensure we're in the right directory
        cd /app
    else
        echo -e "${YELLOW}Running in local environment${NC}"
        # In local environment, ensure we have uv and dependencies
        if ! command -v uv &> /dev/null; then
            echo -e "${RED}Error: uv is not installed. Please install uv first.${NC}"
            exit 1
        fi
        
        # Sync dependencies
        uv sync --dev --no-progress
    fi
    
    echo -e "${GREEN}✓ Python environment ready${NC}"
}

# Function to check if a tool is available (for Python packages)
check_tool_availability() {
    local tool_name="$1"
    local check_cmd="$2"
    
    echo -e "${BLUE}Checking for $tool_name...${NC}"
    if $check_cmd &> /dev/null; then
        echo -e "${GREEN}✓ $tool_name found and working - including $tool_name tests${NC}"
        return 0
    else
        echo -e "${YELLOW}✗ $tool_name not found or not working - skipping $tool_name tests${NC}"
        return 1
    fi
}

# Function to check if a system tool is available
check_system_tool() {
    local tool_name="$1"
    local check_cmd="$2"
    
    echo -e "${BLUE}Checking for $tool_name...${NC}"
    if $check_cmd &> /dev/null; then
        echo -e "${GREEN}✓ $tool_name found and working - including $tool_name tests${NC}"
        return 0
    else
        echo -e "${YELLOW}✗ $tool_name not found or not working - skipping $tool_name tests${NC}"
        return 1
    fi
}

# Function to discover available tools and build test list
discover_tests() {
    echo -e "${BLUE}Discovering available tools for testing...${NC}"
    
    # Check which tools are available and build test file list
    TEST_FILES=()
    
    # Check for all tools using consistent method
    if check_system_tool "darglint" "darglint --version"; then
        TEST_FILES+=("tests/integration/test_darglint_integration.py")
    fi
    
    if check_system_tool "hadolint" "hadolint --version"; then
        TEST_FILES+=("tests/integration/test_hadolint_integration.py")
    fi
    
    if check_system_tool "prettier" "prettier --version"; then
        TEST_FILES+=("tests/integration/test_prettier_integration.py")
    fi
    
    if check_system_tool "ruff" "ruff --version"; then
        TEST_FILES+=("tests/integration/test_ruff_integration.py")
    fi
    
    if check_system_tool "yamllint" "yamllint --version"; then
        TEST_FILES+=("tests/integration/test_yamllint_integration.py")
    fi
    
    # Validate that we have tests to run
    if [ ${#TEST_FILES[@]} -eq 0 ]; then
        echo -e "${RED}No tools available for testing.${NC}"
        echo -e "${YELLOW}Please install at least one of: darglint, hadolint, prettier, ruff, yamllint${NC}"
        echo -e "${YELLOW}You can use './scripts/local-lintro.sh --install' to install missing tools${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Found ${#TEST_FILES[@]} test suite(s) to run${NC}"
    echo -e "${BLUE}Test files: ${TEST_FILES[*]}${NC}"
}

# Function to run tests with coverage
run_tests() {
    echo -e "${BLUE}Running integration tests for available tools...${NC}"
    
    # Use uv run pytest consistently everywhere
    echo -e "${YELLOW}Using uv run pytest for consistent behavior${NC}"
    
    # Prepare coverage arguments
    local coverage_args=(
        "--cov=lintro"
        "--cov-report=term-missing"
        "--cov-report=html"
        "--cov-report=xml"
    )
    
    # Add verbose output if requested
    if [ "$VERBOSE" = "1" ] || [ "$1" = "--verbose" ] || [ "$1" = "-v" ]; then
        coverage_args+=("-v")
        echo -e "${YELLOW}Running tests in verbose mode${NC}"
        shift # Remove verbose flag if it was passed
    fi
    
    # Run tests
    echo -e "${BLUE}Executing: uv run pytest ${TEST_FILES[*]} ${coverage_args[*]}${NC}"
    
    if uv run pytest "${TEST_FILES[@]}" "${coverage_args[@]}"; then
        echo -e "${GREEN}✓ Tests completed successfully${NC}"
        echo ""
        echo -e "${GREEN}Coverage reports generated:${NC}"
        echo -e "  ${BLUE}- Terminal: displayed above${NC}"
        echo -e "  ${BLUE}- HTML: htmlcov/index.html${NC}"
        echo -e "  ${BLUE}- XML: coverage.xml${NC}"
        
        # Show coverage summary if available
        if [ -f "htmlcov/index.html" ]; then
            echo ""
            echo -e "${YELLOW}To view detailed coverage report:${NC}"
            echo -e "  open htmlcov/index.html"
        fi
        
        echo -e "${YELLOW}Debug: Tests completed, about to return${NC}"
        return 0
    else
        echo -e "${RED}✗ Tests failed${NC}"
        return 1
    fi
}

# Function to provide helpful tips
show_tips() {
    echo ""
    echo -e "${YELLOW}=== Helpful Tips ===${NC}"
    echo -e "${BLUE}• Install missing tools: ./scripts/local-lintro.sh --install${NC}"
    echo -e "${BLUE}• Run specific tests: uv run pytest tests/test_ruff_integration.py${NC}"
    echo -e "${BLUE}• Run with verbose output: $0 --verbose${NC}"
    echo -e "${BLUE}• Check tool installation: ./scripts/install-tools.sh --local${NC}"
    echo ""
}

# Main execution flow
main() {
    echo -e "${YELLOW}Debug: Main function called${NC}"
    local exit_code=0
    
    echo -e "${BLUE}=== Lintro Local Test Runner ===${NC}"
    
    # Load environment variables from .env file if it exists
    if [ -f .env ]; then
        echo -e "${YELLOW}Loading environment variables from .env file...${NC}"
        export $(grep -v '^#' .env | xargs)
    fi
    
    # Handle command line arguments
    local verbose=false
    if [ "$1" = "--verbose" ] || [ "$1" = "-v" ]; then
        verbose=true
        VERBOSE=1
        echo -e "${YELLOW}Verbose mode enabled${NC}"
    fi
    
    # Setup Python environment
    setup_python_env
    
    # Discover available tools and tests
    discover_tests
    
    # Run the tests
            if run_tests "$@"; then
            echo -e "${GREEN}=== All tests passed! ===${NC}"
            exit_code=0
            
            # Copy coverage files to /code if we're in Docker and /code exists
            echo -e "${YELLOW}Debug: RUNNING_IN_DOCKER=$RUNNING_IN_DOCKER${NC}"
            echo -e "${YELLOW}Debug: /code directory exists: $([ -d "/code" ] && echo "yes" || echo "no")${NC}"
            echo -e "${YELLOW}Debug: Current directory: $(pwd)${NC}"
            echo -e "${YELLOW}Debug: Current user: $(whoami)${NC}"
            
            # Small delay to ensure files are fully written
            if [ -d "/code" ] && [ "$(pwd)" = "/app" ]; then
                echo -e "${YELLOW}Waiting for files to be fully written...${NC}"
                sleep 1
            fi
            if [ -d "/code" ] && [ "$(pwd)" = "/app" ]; then
                echo -e "${BLUE}Copying coverage files to host directory...${NC}"
                echo -e "${YELLOW}Current directory: $(pwd)${NC}"
                echo -e "${YELLOW}Files in current directory:${NC}"
                ls -la coverage.xml htmlcov/ 2>/dev/null || echo "Coverage files not found in current directory"
                
                # Fix permissions on /code directory if running as root
                if [ "$(whoami)" = "root" ]; then
                    echo -e "${YELLOW}Fixing permissions on /code directory...${NC}"
                    chown -R root:root /code 2>/dev/null || true
                    chmod -R 755 /code 2>/dev/null || true
                fi
                
                # Copy htmlcov directory
                echo -e "${YELLOW}Copying htmlcov to /code...${NC}"
                if [ -d "htmlcov" ]; then
                    cp -rv htmlcov/ /code/ 2>&1 && echo -e "${GREEN}✓ htmlcov copied successfully${NC}" || echo -e "${RED}✗ Could not copy htmlcov${NC}"
                else
                    echo -e "${RED}✗ htmlcov directory not found${NC}"
                fi
                
                # Copy coverage.xml file
                echo -e "${YELLOW}Copying coverage.xml to /code...${NC}"
                if [ -f "coverage.xml" ]; then
                    cp -v coverage.xml /code/ 2>&1 && echo -e "${GREEN}✓ coverage.xml copied successfully${NC}" || echo -e "${RED}✗ Could not copy coverage.xml${NC}"
                else
                    echo -e "${RED}✗ coverage.xml file not found${NC}"
                fi
                
                # Copy .coverage file
                echo -e "${YELLOW}Copying .coverage to /code...${NC}"
                if [ -f ".coverage" ]; then
                    cp -v .coverage /code/ 2>&1 && echo -e "${GREEN}✓ .coverage copied successfully${NC}" || echo -e "${RED}✗ Could not copy .coverage${NC}"
                else
                    echo -e "${RED}✗ .coverage file not found${NC}"
                fi
                
                # Verify files were copied
                echo -e "${YELLOW}Verifying files in /code after copy:${NC}"
                if [ -f "/code/coverage.xml" ]; then
                    echo -e "${GREEN}✓ /code/coverage.xml exists (size: $(wc -c < /code/coverage.xml) bytes)${NC}"
                else
                    echo -e "${RED}✗ /code/coverage.xml not found${NC}"
                fi
                
                if [ -d "/code/htmlcov" ]; then
                    echo -e "${GREEN}✓ /code/htmlcov directory exists${NC}"
                else
                    echo -e "${RED}✗ /code/htmlcov directory not found${NC}"
                fi
                
                echo -e "${GREEN}✓ Coverage files copy process completed${NC}"
            fi
        else
            echo -e "${RED}=== Tests failed! ===${NC}"
            exit_code=1
        fi
    
    # Show helpful tips
    show_tips
    
    exit $exit_code
}

# Show usage information
show_usage() {
    echo "Usage: $0 [--verbose|-v]"
    echo ""
    echo "This script automatically:"
    echo "  1. Sets up the Python environment"
    echo "  2. Discovers available linting tools"
    echo "  3. Runs integration tests for available tools"
    echo "  4. Generates coverage reports"
    echo ""
    echo "Options:"
    echo "  --verbose, -v    Run tests with verbose output"
    echo ""
    echo "The script will automatically skip tests for tools that aren't installed."
    echo "Use './scripts/local-lintro.sh --install' to install missing tools."
}

# Handle help request
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_usage
    exit 0
fi

# Run main function
main "$@" 