"""Tests for BlackPlugin.set_options method."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.black import BlackPlugin


# Tests for valid options


@pytest.mark.parametrize(
    ("option_name", "option_value"),
    [
        ("line_length", 80),
        ("line_length", 120),
        ("target_version", "py310"),
        ("target_version", "py313"),
        ("fast", True),
        ("fast", False),
        ("preview", True),
        ("preview", False),
        ("diff", True),
        ("diff", False),
    ],
    ids=[
        "line_length_80",
        "line_length_120",
        "target_version_py310",
        "target_version_py313",
        "fast_true",
        "fast_false",
        "preview_true",
        "preview_false",
        "diff_true",
        "diff_false",
    ],
)
def test_set_options_valid(
    black_plugin: BlackPlugin,
    option_name: str,
    option_value: object,
) -> None:
    """Set valid options correctly.

    Args:
        black_plugin: The BlackPlugin instance to test.
        option_name: The name of the option to set.
        option_value: The value to set for the option.
    """
    black_plugin.set_options(**{option_name: option_value})  # type: ignore[arg-type]
    assert_that(black_plugin.options.get(option_name)).is_equal_to(option_value)


# Tests for invalid types


@pytest.mark.parametrize(
    ("option_name", "invalid_value", "error_match"),
    [
        ("line_length", "eighty", "line_length must be an integer"),
        ("line_length", 10.5, "line_length must be an integer"),
        ("target_version", 310, "target_version must be a string"),
        ("fast", "yes", "fast must be a boolean"),
        ("fast", 1, "fast must be a boolean"),
        ("preview", "yes", "preview must be a boolean"),
        ("diff", "yes", "diff must be a boolean"),
    ],
    ids=[
        "invalid_line_length_string",
        "invalid_line_length_float",
        "invalid_target_version_int",
        "invalid_fast_string",
        "invalid_fast_int",
        "invalid_preview_string",
        "invalid_diff_string",
    ],
)
def test_set_options_invalid_type(
    black_plugin: BlackPlugin,
    option_name: str,
    invalid_value: object,
    error_match: str,
) -> None:
    """Raise ValueError for invalid option types.

    Args:
        black_plugin: The BlackPlugin instance to test.
        option_name: The name of the option to test.
        invalid_value: An invalid value for the option.
        error_match: Expected error message pattern.
    """
    with pytest.raises(ValueError, match=error_match):
        black_plugin.set_options(**{option_name: invalid_value})  # type: ignore[arg-type]
