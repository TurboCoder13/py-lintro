"""Tests for is_tool_injectable function."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.utils.unified_config import is_tool_injectable


@pytest.mark.parametrize(
    "tool_name",
    ["ruff", "black", "markdownlint", "yamllint"],
    ids=["ruff", "black", "markdownlint", "yamllint"],
)
def test_is_tool_injectable_returns_true_for_injectable_tools(tool_name: str) -> None:
    """Verify injectable tools are correctly identified.

    Args:
        tool_name: Name of the tool.
    """
    assert_that(is_tool_injectable(tool_name)).is_true()


@pytest.mark.parametrize(
    "tool_name",
    ["RUFF", "Black", "MarkdownLint"],
    ids=["RUFF_upper", "Black_mixed", "MarkdownLint_mixed"],
)
def test_is_tool_injectable_is_case_insensitive(tool_name: str) -> None:
    """Verify tool name matching is case-insensitive.

    Args:
        tool_name: Name of the tool.
    """
    assert_that(is_tool_injectable(tool_name)).is_true()


def test_is_tool_injectable_returns_false_for_unknown_tool() -> None:
    """Verify unknown tools are not marked as injectable."""
    assert_that(is_tool_injectable("unknown_tool")).is_false()


def test_is_tool_injectable_returns_false_for_non_injectable_known_tools() -> None:
    """Verify known non-injectable tools return False."""
    assert_that(is_tool_injectable("bandit")).is_false()
