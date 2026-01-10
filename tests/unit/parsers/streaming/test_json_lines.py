"""Tests for stream_json_lines function."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from assertpy import assert_that

from lintro.parsers.streaming import stream_json_lines

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.unit.parsers.streaming.conftest import SimpleIssue


def test_parses_string(
    parse_test_item: Callable[[dict[str, object]], SimpleIssue | None],
) -> None:
    """Parse newline-separated JSON objects from string.

    Args:
        parse_test_item: Fixture providing a parser function for test items.
    """
    output = (
        '{"file": "a.py", "message": "error1"}\n{"file": "b.py", "message": "error2"}\n'
    )
    results = list(stream_json_lines(output, parse_test_item))

    assert_that(results).is_length(2)
    assert_that(results[0].file).is_equal_to("a.py")
    assert_that(results[1].file).is_equal_to("b.py")


def test_parses_iterable(
    parse_test_item: Callable[[dict[str, object]], SimpleIssue | None],
) -> None:
    """Parse JSON objects from line iterable.

    Args:
        parse_test_item: Fixture providing a parser function for test items.
    """
    lines = [
        '{"file": "c.py", "message": "msg1"}',
        '{"file": "d.py", "message": "msg2"}',
    ]
    results = list(stream_json_lines(lines, parse_test_item))

    assert_that(results).is_length(2)
    assert_that(results[0].file).is_equal_to("c.py")
    assert_that(results[1].file).is_equal_to("d.py")


def test_skips_empty_lines(
    parse_test_item: Callable[[dict[str, object]], SimpleIssue | None],
) -> None:
    """Skip empty lines in output.

    Args:
        parse_test_item: Fixture providing a parser function for test items.
    """
    output = '{"file": "a.py"}\n\n\n{"file": "b.py"}\n'
    results = list(stream_json_lines(output, parse_test_item))

    assert_that(results).is_length(2)


def test_skips_non_json_lines(
    parse_test_item: Callable[[dict[str, object]], SimpleIssue | None],
) -> None:
    """Skip lines that don't start with opening brace.

    Args:
        parse_test_item: Fixture providing a parser function for test items.
    """
    output = 'some info\n{"file": "a.py"}\nmore text\n'
    results = list(stream_json_lines(output, parse_test_item))

    assert_that(results).is_length(1)
    assert_that(results[0].file).is_equal_to("a.py")


def test_handles_invalid_json(
    parse_test_item: Callable[[dict[str, object]], SimpleIssue | None],
) -> None:
    """Handle invalid JSON gracefully without raising.

    Args:
        parse_test_item: Fixture providing a parser function for test items.
    """
    output = '{"file": "a.py"}\n{invalid json}\n{"file": "b.py"}\n'
    results = list(stream_json_lines(output, parse_test_item))

    assert_that(results).is_length(2)


@pytest.mark.parametrize(
    "output",
    [
        "",
        "\n",
        "\n\n\n",
    ],
)
def test_empty_output_yields_nothing(
    output: str,
    parse_test_item: Callable[[dict[str, object]], SimpleIssue | None],
) -> None:
    """Empty or whitespace-only output yields no results.

    Args:
        output: Parameterized output string to parse.
        parse_test_item: Fixture providing a parser function for test items.
    """
    results = list(stream_json_lines(output, parse_test_item))

    assert_that(results).is_empty()


def test_skips_items_where_parser_returns_none(
    parse_test_item: Callable[[dict[str, object]], SimpleIssue | None],
) -> None:
    """Skip items when parse function returns None.

    Args:
        parse_test_item: Fixture providing a parser function for test items.
    """

    def selective_parser(item: dict[str, object]) -> SimpleIssue | None:
        if item.get("skip"):
            return None
        return parse_test_item(item)

    output = '{"file": "a.py"}\n{"file": "b.py", "skip": true}\n{"file": "c.py"}\n'
    results = list(stream_json_lines(output, selective_parser))

    assert_that(results).is_length(2)
    assert_that(results[0].file).is_equal_to("a.py")
    assert_that(results[1].file).is_equal_to("c.py")
