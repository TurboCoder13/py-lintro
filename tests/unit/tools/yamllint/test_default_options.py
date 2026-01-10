"""Tests for YamllintPlugin default_options property."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from assertpy import assert_that

from lintro.tools.definitions.yamllint import YAMLLINT_DEFAULT_TIMEOUT

if TYPE_CHECKING:
    from lintro.tools.definitions.yamllint import YamllintPlugin


@pytest.mark.parametrize(
    ("option_name", "expected_value"),
    [
        ("timeout", YAMLLINT_DEFAULT_TIMEOUT),
        ("format", "parsable"),
        ("config_file", None),
        ("config_data", None),
        ("strict", False),
        ("relaxed", False),
        ("no_warnings", False),
    ],
    ids=[
        "timeout_equals_default",
        "format_is_parsable",
        "config_file_is_none",
        "config_data_is_none",
        "strict_is_false",
        "relaxed_is_false",
        "no_warnings_is_false",
    ],
)
def test_default_options_values(
    yamllint_plugin: YamllintPlugin,
    option_name: str,
    expected_value: Any,
) -> None:
    """Default options have correct values.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
        option_name: The name of the option to test.
        expected_value: The expected default value for the option.
    """
    assert_that(yamllint_plugin.definition.default_options[option_name]).is_equal_to(
        expected_value,
    )
