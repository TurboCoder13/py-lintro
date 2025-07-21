"""Test fixtures for formatters tests.

This module provides shared fixtures for testing formatter utilities in Lintro.
"""

import pytest
from unittest.mock import MagicMock
from lintro.models.core.tool_result import ToolResult


@pytest.fixture
def sample_tool_result():
    """Provide a sample tool result for testing.

    Returns:
        ToolResult: A sample ToolResult object.
    """
    tool = MagicMock()
    tool.name = "test_tool"
    tool.priority = 1

    return ToolResult(
        name="test_tool",
        success=True,
        output="",
        issues_count=0,
    )


@pytest.fixture
def sample_tool_results():
    """Provide sample tool results for testing.

    Returns:
        list[ToolResult]: List of sample ToolResult objects.
    """
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
