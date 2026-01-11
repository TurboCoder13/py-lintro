"""Tests for ToolOrderStrategy enum."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.utils.unified_config import ToolOrderStrategy


@pytest.mark.parametrize(
    ("strategy", "expected_value"),
    [
        (ToolOrderStrategy.PRIORITY, "priority"),
        (ToolOrderStrategy.ALPHABETICAL, "alphabetical"),
        (ToolOrderStrategy.CUSTOM, "custom"),
    ],
    ids=["priority", "alphabetical", "custom"],
)
def test_tool_order_strategy_enum_values(
    strategy: ToolOrderStrategy,
    expected_value: str,
) -> None:
    """Verify ToolOrderStrategy enum members have expected string values.

    Args:
        strategy: Configuration strategy.
        expected_value: Expected value.
    """
    assert_that(strategy.value).is_equal_to(expected_value)


def test_tool_order_strategy_is_str_enum() -> None:
    """Verify ToolOrderStrategy members can be used as strings."""
    assert_that(ToolOrderStrategy.PRIORITY).is_equal_to("priority")
    assert_that(str(ToolOrderStrategy.ALPHABETICAL)).is_equal_to("alphabetical")
