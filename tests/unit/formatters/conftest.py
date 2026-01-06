"""Shared fixtures for formatter unit tests."""

from __future__ import annotations

import pytest

from lintro.models.core.tool_result import ToolResult


@pytest.fixture
def sample_tool_result() -> ToolResult:
    """Provide a sample tool result for testing.

    Returns:
        ToolResult: Sample tool result instance.
    """
    return ToolResult(
        name="test_tool",
        success=True,
        output="",
        issues_count=0,
    )


@pytest.fixture
def sample_tool_results() -> list[ToolResult]:
    """Provide sample tool results for testing.

    Returns:
        list[ToolResult]: List of sample tool result instances.
    """
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
