#!/usr/bin/env bash
set -euo pipefail

# update-coverage-badge.sh - Update coverage badge locally
#
# This script updates the coverage badge based on the current coverage.xml file.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../utils/utils.sh
source "$SCRIPT_DIR/../utils/utils.sh"

# Show help if requested
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
	echo "Usage: $0 [--help]"
	echo ""
	echo "Update Coverage Badge Script"
	echo "Updates the coverage badge based on current coverage.xml file."
	echo ""
	echo "This script:"
	echo "  - Extracts coverage percentage from coverage.xml"
	echo "  - Generates SVG badge with appropriate color"
	echo "  - Updates assets/images/coverage-badge.svg file"
	echo ""
	echo "Prerequisites:"
	echo "  - coverage.xml file must exist (run tests first)"
	echo "  - uv must be available"
	echo ""
	echo "Examples:"
	echo "  $0                    # Update badge from coverage.xml"
	echo "  ./scripts/local/run-tests.sh && $0  # Run tests then update badge"
	exit 0
fi

echo -e "${BLUE}=== Coverage Badge Update ===${NC}"

# Check if coverage.xml exists
if [ ! -f "coverage.xml" ]; then
	echo -e "${RED}Error: coverage.xml not found${NC}"
	echo -e "${YELLOW}Please run tests first to generate coverage data:${NC}"
	echo -e "  ./scripts/local/run-tests.sh"
	exit 1
fi

# Run the coverage badge update script
echo -e "${BLUE}Updating coverage badge...${NC}"
if ./scripts/ci/coverage-badge-update.sh; then
	echo -e "${GREEN}✓ Coverage badge updated successfully${NC}"
	echo -e "${BLUE}Badge file: assets/images/coverage-badge.svg${NC}"
else
	echo -e "${RED}✗ Failed to update coverage badge${NC}"
	exit 1
fi
