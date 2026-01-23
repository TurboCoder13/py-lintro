"""Tests for get_ordered_tools function."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from assertpy import assert_that

from lintro.utils.unified_config import get_ordered_tools


def test_get_ordered_tools_priority_ordering(mock_empty_tool_order_config: Any) -> None:
    """Verify tools are ordered by priority (lower values first).

    Args:
        mock_empty_tool_order_config: Mock empty tool order configuration.
    """
    result = get_ordered_tools(["ruff", "black", "bandit"])
    assert_that(result).is_equal_to(["black", "ruff", "bandit"])


def test_get_ordered_tools_alphabetical_ordering() -> None:
    """Verify alphabetical ordering when strategy is 'alphabetical'."""
    result = get_ordered_tools(["ruff", "black", "bandit"], tool_order="alphabetical")
    assert_that(result).is_equal_to(["bandit", "black", "ruff"])


def test_get_ordered_tools_custom_ordering() -> None:
    """Verify custom ordering puts specified tools first."""
    result = get_ordered_tools(
        ["ruff", "black", "bandit", "mypy"],
        tool_order=["mypy", "bandit"],
    )
    assert_that(result[0]).is_equal_to("mypy")
    assert_that(result[1]).is_equal_to("bandit")
    # Remaining tools should be ordered by priority
    assert_that(result).is_length(4)


def test_get_ordered_tools_invalid_strategy_falls_back_to_priority() -> None:
    """Verify invalid strategy argument falls back to priority ordering."""
    result = get_ordered_tools(
        ["ruff", "black", "bandit"],
        tool_order="invalid_strategy",
    )
    assert_that(result).is_equal_to(["black", "ruff", "bandit"])


def test_get_ordered_tools_invalid_config_strategy_falls_back_to_priority() -> None:
    """Verify invalid strategy in config falls back to priority ordering."""
    with patch(
        "lintro.utils.unified_config.get_tool_order_config",
        return_value={"strategy": "invalid_strategy"},
    ):
        result = get_ordered_tools(["ruff", "black", "bandit"])
        assert_that(result).is_equal_to(["black", "ruff", "bandit"])
