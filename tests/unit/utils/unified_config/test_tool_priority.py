"""Tests for get_tool_priority function."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.utils.unified_config import get_tool_priority


@pytest.mark.parametrize(
    ("tool_name", "expected_priority"),
    [
        ("prettier", 10),
        ("black", 15),
        ("ruff", 20),
        ("markdownlint", 30),
        ("yamllint", 35),
        ("bandit", 45),
        ("pytest", 100),
    ],
    ids=[
        "prettier",
        "black",
        "ruff",
        "markdownlint",
        "yamllint",
        "bandit",
        "pytest",
    ],
)
def test_get_tool_priority_returns_default_values(
    mock_empty_tool_order_config: Any,
    tool_name: str,
    expected_priority: int,
) -> None:
    """Verify default priorities for known tools.

    Args:
        mock_empty_tool_order_config: Mock empty tool order configuration.
        tool_name: Name of the tool.
        expected_priority: Expected priority value.
    """
    result = get_tool_priority(tool_name)
    assert_that(result).is_equal_to(expected_priority)


def test_get_tool_priority_unknown_tool_returns_50(
    mock_empty_tool_order_config: Any,
) -> None:
    """Verify unknown tools get default priority of 50.

    Args:
        mock_empty_tool_order_config: Mock empty tool order configuration.
    """
    result = get_tool_priority("unknown_tool")
    assert_that(result).is_equal_to(50)


def test_get_tool_priority_respects_override() -> None:
    """Verify priority overrides from config take precedence."""
    with patch(
        "lintro.utils.config_priority.get_tool_order_config",
        return_value={"priority_overrides": {"ruff": 5}},
    ):
        result = get_tool_priority("ruff")
        assert_that(result).is_equal_to(5)


def test_get_tool_priority_override_is_case_insensitive() -> None:
    """Verify priority override keys are case-insensitive."""
    with patch(
        "lintro.utils.config_priority.get_tool_order_config",
        return_value={"priority_overrides": {"RUFF": 5}},
    ):
        result = get_tool_priority("ruff")
        assert_that(result).is_equal_to(5)
