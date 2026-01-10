"""Tests for _get_nested_value function."""

from __future__ import annotations

from typing import Any

import pytest
from assertpy import assert_that

from lintro.utils.unified_config import _get_nested_value


@pytest.mark.parametrize(
    ("config", "key_path", "expected"),
    [
        ({"line-length": 100}, "line-length", 100),
        ({"rules": {"line-length": {"max": 100}}}, "rules.line-length.max", 100),
        ({"a": {"b": {"c": "deep"}}}, "a.b.c", "deep"),
        ({"key": "value"}, "key", "value"),
    ],
    ids=["simple_key", "nested_three_levels", "deeply_nested", "string_value"],
)
def test_get_nested_value_returns_expected_value(
    config: dict[str, Any],
    key_path: str,
    expected: Any,
) -> None:
    """Verify _get_nested_value retrieves values at various nesting depths.

    Args:
        config: Configuration object.
        key_path: Path to configuration key.
        expected: Expected value.
    """
    result = _get_nested_value(config, key_path)
    assert_that(result).is_equal_to(expected)


@pytest.mark.parametrize(
    ("config", "key_path"),
    [
        ({"other": "value"}, "line-length"),
        ({"rules": {"other": "value"}}, "rules.line-length.max"),
        ({}, "any.key"),
        ({"rules": "not a dict"}, "rules.line-length.max"),
    ],
    ids=[
        "missing_top_level",
        "missing_nested",
        "empty_config",
        "non_dict_intermediate",
    ],
)
def test_get_nested_value_returns_none_for_missing_keys(
    config: dict[str, Any],
    key_path: str,
) -> None:
    """Verify _get_nested_value returns None when path doesn't exist.

    Args:
        config: Configuration object.
        key_path: Path to configuration key.
    """
    result = _get_nested_value(config, key_path)
    assert_that(result).is_none()
