"""Tests for pydoclint parser handling of invalid/empty input."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.parsers.pydoclint.pydoclint_parser import parse_pydoclint_output


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
        output: The pydoclint output to parse.
    """
    result = parse_pydoclint_output(output=output)
    assert_that(result).is_empty()


def test_parse_returns_empty_for_malformed_line() -> None:
    """Parse malformed lines returns empty list."""
    result = parse_pydoclint_output(output="this is not valid output")
    assert_that(result).is_empty()


def test_parse_returns_empty_for_missing_code() -> None:
    """Parse line without DOC code returns empty list."""
    result = parse_pydoclint_output(output="test.py:10:5: Missing code message")
    assert_that(result).is_empty()


def test_parse_skips_malformed_lines_in_mixed_output() -> None:
    """Parse mixed valid and invalid lines only returns valid issues."""
    output = """test.py
    10: DOC101: Valid issue
malformed line without proper format
another.py
    20: DOC201: Another valid issue
"""
    result = parse_pydoclint_output(output=output)

    assert_that(result).is_length(2)
    assert_that(result[0].code).is_equal_to("DOC101")
    assert_that(result[1].code).is_equal_to("DOC201")


def test_parse_handles_missing_line_number() -> None:
    """Parse issue line without proper line number returns empty."""
    output = """test.py
    : DOC101: Message without line number"""
    result = parse_pydoclint_output(output=output)
    assert_that(result).is_empty()
