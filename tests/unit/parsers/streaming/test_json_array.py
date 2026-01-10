"""Tests for stream_json_array_fallback function."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from assertpy import assert_that

from lintro.parsers.streaming import stream_json_array_fallback

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.unit.parsers.streaming.conftest import SimpleIssue


def test_parses_array(
    parse_test_item: Callable[[dict[str, object]], SimpleIssue | None],
) -> None:
    """Parse standard JSON array.

    Args:
        parse_test_item: Fixture providing a parser function for test items.
    """
    output = '[{"file": "a.py"}, {"file": "b.py"}]'
    results = list(stream_json_array_fallback(output, parse_test_item))

    assert_that(results).is_length(2)
    assert_that(results[0].file).is_equal_to("a.py")
    assert_that(results[1].file).is_equal_to("b.py")


def test_parses_with_trailing_data(
    parse_test_item: Callable[[dict[str, object]], SimpleIssue | None],
) -> None:
    """Parse JSON array with trailing non-JSON data.

    Args:
        parse_test_item: Fixture providing a parser function for test items.
    """
    output = '[{"file": "a.py"}]\nSome extra text'
    results = list(stream_json_array_fallback(output, parse_test_item))

    assert_that(results).is_length(1)
    assert_that(results[0].file).is_equal_to("a.py")


def test_falls_back_to_json_lines(
    parse_test_item: Callable[[dict[str, object]], SimpleIssue | None],
) -> None:
    """Fall back to JSON Lines when array parsing fails.

    Args:
        parse_test_item: Fixture providing a parser function for test items.
    """
    output = '{"file": "a.py"}\n{"file": "b.py"}\n'
    results = list(stream_json_array_fallback(output, parse_test_item))

    assert_that(results).is_length(2)


@pytest.mark.parametrize(
    "output",
    [
        "[]",
        "{}",
        "",
    ],
)
def test_empty_yields_nothing(
    output: str,
    parse_test_item: Callable[[dict[str, object]], SimpleIssue | None],
) -> None:
    """Empty array, object, or string yields no results.

    Args:
        output: Parameterized output string to parse.
        parse_test_item: Fixture providing a parser function for test items.
    """
    results = list(stream_json_array_fallback(output, parse_test_item))

    assert_that(results).is_empty()
