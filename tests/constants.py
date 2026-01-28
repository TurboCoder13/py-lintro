"""Test constants for the lintro test suite.

This module provides commonly used constants to avoid magic numbers
in test files and ensure consistency across tests.
"""

from __future__ import annotations

# =============================================================================
# Exit Codes
# =============================================================================

EXIT_SUCCESS: int = 0
EXIT_FAILURE: int = 1

# =============================================================================
# Timeouts (in seconds)
# =============================================================================

# Default timeout for most tool operations
DEFAULT_TOOL_TIMEOUT: int = 30

# Short timeout for quick operations (yamllint, etc.)
SHORT_TOOL_TIMEOUT: int = 15

# Extended timeout for slower tools (pytest, etc.)
LONG_TOOL_TIMEOUT: int = 300

# Integration test CLI timeout
CLI_TIMEOUT: int = 60

# Quick CLI operations (version checks, etc.)
QUICK_CLI_TIMEOUT: int = 10

# =============================================================================
# Tool-Specific Timeouts
# =============================================================================

PYTEST_DEFAULT_TIMEOUT: int = 300
RUFF_DEFAULT_TIMEOUT: int = 30
YAMLLINT_DEFAULT_TIMEOUT: int = 15

# =============================================================================
# Test Limits
# =============================================================================

# Minimum expected number of tools in the registry
MIN_EXPECTED_TOOLS: int = 13

# Default line length for tests
DEFAULT_LINE_LENGTH: int = 88
