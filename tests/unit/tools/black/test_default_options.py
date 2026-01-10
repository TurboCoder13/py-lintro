"""Tests for BlackPlugin default options."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from assertpy import assert_that

from lintro.tools.definitions.black import BLACK_DEFAULT_TIMEOUT

if TYPE_CHECKING:
    from lintro.tools.definitions.black import BlackPlugin


def test_default_options_timeout(black_plugin: BlackPlugin) -> None:
    """Default options include timeout.

    Args:
        black_plugin: The BlackPlugin instance to test.
    """
    assert_that(black_plugin.definition.default_options["timeout"]).is_equal_to(
        BLACK_DEFAULT_TIMEOUT,
    )


@pytest.mark.parametrize(
    ("option_name", "expected_value"),
    [
        ("line_length", None),
        ("target_version", None),
        ("fast", False),
        ("preview", False),
        ("diff", False),
    ],
    ids=[
        "line_length_is_none",
        "target_version_is_none",
        "fast_is_false",
        "preview_is_false",
        "diff_is_false",
    ],
)
def test_default_options_values(
    black_plugin: BlackPlugin,
    option_name: str,
    expected_value: Any,
) -> None:
    """Default options have correct values.

    Args:
        black_plugin: The BlackPlugin instance to test.
        option_name: The name of the option to check.
        expected_value: The expected value for the option.
    """
    assert_that(
        black_plugin.definition.default_options[option_name],
    ).is_equal_to(expected_value)
