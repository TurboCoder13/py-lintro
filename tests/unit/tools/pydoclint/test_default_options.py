"""Tests for pydoclint plugin default options."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.tools.definitions.pydoclint import (
    PYDOCLINT_DEFAULT_STYLE,
    PYDOCLINT_DEFAULT_TIMEOUT,
    PydoclintPlugin,
)


@pytest.mark.parametrize(
    ("option_name", "expected_value"),
    [
        ("timeout", PYDOCLINT_DEFAULT_TIMEOUT),
        ("style", PYDOCLINT_DEFAULT_STYLE),
        ("check_return_types", True),
        ("check_arg_order", True),
        ("skip_checking_short_docstrings", True),
        ("quiet", True),
    ],
    ids=[
        "timeout_equals_default",
        "style_equals_default",
        "check_return_types_is_true",
        "check_arg_order_is_true",
        "skip_checking_short_docstrings_is_true",
        "quiet_is_true",
    ],
)
def test_default_options_values(
    pydoclint_plugin: PydoclintPlugin,
    option_name: str,
    expected_value: object,
) -> None:
    """Default options have correct values.

    Args:
        pydoclint_plugin: The PydoclintPlugin instance to test.
        option_name: The name of the option to check.
        expected_value: The expected value for the option.
    """
    assert_that(
        pydoclint_plugin.definition.default_options[option_name],
    ).is_equal_to(expected_value)
