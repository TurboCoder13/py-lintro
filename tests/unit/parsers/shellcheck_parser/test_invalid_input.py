"""Tests for shellcheck parser handling of invalid/empty input."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.parsers.shellcheck.shellcheck_parser import parse_shellcheck_output


@pytest.mark.parametrize(
    "output",
    [
        None,
        "",
        "   \n  \n   ",
    ],
    ids=["none", "empty", "whitespace_only"],
)
def test_parse_returns_empty_for_no_content(
    output: str | None,
) -> None:
    """Parse empty, None, or whitespace-only output returns empty list.

    Args:
        output: The shellcheck output to parse.
    """
    result = parse_shellcheck_output(output=output)
    assert_that(result).is_empty()


def test_parse_returns_empty_for_invalid_json() -> None:
    """Parse invalid JSON returns empty list."""
    result = parse_shellcheck_output(output="not valid json")
    assert_that(result).is_empty()


def test_parse_returns_empty_for_non_array_json() -> None:
    """Parse JSON that is not an array returns empty list."""
    result = parse_shellcheck_output(output='{"key": "value"}')
    assert_that(result).is_empty()


def test_parse_empty_array() -> None:
    """Parse empty JSON array returns empty list."""
    result = parse_shellcheck_output(output="[]")
    assert_that(result).is_empty()
