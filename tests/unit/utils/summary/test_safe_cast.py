"""Unit tests for _safe_cast function in summary_tables module.

Tests cover type conversion with fallbacks for int and float values,
and error handling for invalid inputs.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.utils.summary_tables import _safe_cast

# =============================================================================
# Tests for _safe_cast function
# =============================================================================


@pytest.mark.parametrize(
    ("value", "converter", "default", "expected"),
    [
        ("42", int, 0, 42),
        ("100", int, -1, 100),
        ("0", int, 99, 0),
    ],
    ids=["basic-int", "with-different-default", "zero-value"],
)
def test_safe_cast_successful_int_cast(
    value: str,
    converter: type,
    default: int,
    expected: int,
) -> None:
    """Cast string to int successfully with various inputs.

    Args:
        value: String value to cast.
        converter: Value converter function.
        default: Default value.
        expected: Expected result after casting.
    """
    summary = {"count": value}
    with patch("lintro.utils.summary_tables.get_summary_value", return_value=value):
        result = _safe_cast(summary, "count", default, converter)
    assert_that(result).is_equal_to(expected)


@pytest.mark.parametrize(
    ("value", "default", "expected"),
    [
        ("1.5", 0.0, 1.5),
        ("3.14159", 0.0, 3.14159),
        ("0.0", 1.0, 0.0),
    ],
    ids=["basic-float", "pi-value", "zero-float"],
)
def test_safe_cast_successful_float_cast(
    value: str,
    default: float,
    expected: float,
) -> None:
    """Cast string to float successfully with various inputs.

    Args:
        value: String value to cast.
        default: Default value.
        expected: Expected result after casting.
    """
    summary = {"duration": value}
    with patch("lintro.utils.summary_tables.get_summary_value", return_value=value):
        result = _safe_cast(summary, "duration", default, float)
    assert_that(result).is_equal_to(expected)


@pytest.mark.parametrize(
    ("value", "default"),
    [
        ("not_a_number", -1),
        ("abc", 0),
        ("12.34.56", 100),
    ],
    ids=["text-value", "letters-only", "malformed-number"],
)
def test_safe_cast_returns_default_on_value_error(value: str, default: int) -> None:
    """Return default when value cannot be converted due to ValueError.

    Args:
        value: Value to test.
        default: Default value to return.
    """
    summary = {"count": value}
    with patch("lintro.utils.summary_tables.get_summary_value", return_value=value):
        result = _safe_cast(summary, "count", default, int)
    assert_that(result).is_equal_to(default)


@pytest.mark.parametrize(
    ("value", "default"),
    [
        (None, 0),
        (None, -1),
        (None, 999),
    ],
    ids=["default-zero", "default-negative", "default-large"],
)
def test_safe_cast_returns_default_on_type_error(value: Any, default: int) -> None:
    """Return default when value causes TypeError during conversion.

    Args:
        value: Value that causes TypeError.
        default: Default value to return.
    """
    summary = {"count": value}
    with patch("lintro.utils.summary_tables.get_summary_value", return_value=value):
        result = _safe_cast(summary, "count", default, int)
    assert_that(result).is_equal_to(default)
