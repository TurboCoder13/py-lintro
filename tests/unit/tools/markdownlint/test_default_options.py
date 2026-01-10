"""Tests for markdownlint default options."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from assertpy import assert_that

from lintro.tools.definitions.markdownlint import MARKDOWNLINT_DEFAULT_TIMEOUT

if TYPE_CHECKING:
    from lintro.tools.definitions.markdownlint import MarkdownlintPlugin


@pytest.mark.parametrize(
    ("option_name", "expected_value"),
    [
        ("timeout", MARKDOWNLINT_DEFAULT_TIMEOUT),
        ("line_length", None),
    ],
    ids=[
        "timeout_equals_default",
        "line_length_is_none",
    ],
)
def test_default_options_values(
    markdownlint_plugin: MarkdownlintPlugin,
    option_name: str,
    expected_value: object,
) -> None:
    """Default options have correct values.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
        option_name: The name of the option to test.
        expected_value: The expected default value for the option.
    """
    assert_that(markdownlint_plugin.definition.default_options).contains_key(
        option_name,
    )
    assert_that(
        markdownlint_plugin.definition.default_options[option_name],
    ).is_equal_to(expected_value)
