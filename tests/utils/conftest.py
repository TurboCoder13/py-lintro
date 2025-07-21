"""Test fixtures for utils tests.

This module provides shared fixtures for testing utility functions in Lintro.
"""

import pytest
from unittest.mock import MagicMock
from lintro.models.core.tool_result import ToolResult


@pytest.fixture
def sample_tool_results():
    """Provide sample tool results for testing.

    Returns:
        list[ToolResult]: List of sample ToolResult objects.
    """
    # Create mock tools
    tool1 = MagicMock()
    tool1.name = "ruff"
    tool1.priority = 1

    tool2 = MagicMock()
    tool2.name = "yamllint"
    tool2.priority = 2

    result1 = ToolResult(
        name="ruff",
        success=True,
        output="",
        issues_count=0,
    )
    result2 = ToolResult(
        name="yamllint",
        success=False,
        output="",
        issues_count=2,
    )

    return [result1, result2]
