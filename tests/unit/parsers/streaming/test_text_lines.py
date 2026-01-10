"""Tests for stream_text_lines function."""

from __future__ import annotations

from typing import TYPE_CHECKING

from assertpy import assert_that

from lintro.parsers.streaming import stream_text_lines

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.unit.parsers.streaming.conftest import SimpleIssue


def test_parses_string(
    parse_error_line: Callable[[str], SimpleIssue | None],
) -> None:
    """Parse lines from string.

    Args:
        parse_error_line: Fixture providing parser function for error lines.
    """
    output = "INFO: ok\nERROR: bad thing\nINFO: fine\nERROR: another\n"
    results = list(stream_text_lines(output, parse_error_line))

    assert_that(results).is_length(2)
    assert_that(results[0].message).is_equal_to("bad thing")
    assert_that(results[1].message).is_equal_to("another")


def test_parses_iterable(
    parse_error_line: Callable[[str], SimpleIssue | None],
) -> None:
    """Parse lines from iterable.

    Args:
        parse_error_line: Fixture providing parser function for error lines.
    """
    lines = ["ERROR: first", "OK", "ERROR: second"]
    results = list(stream_text_lines(lines, parse_error_line))

    assert_that(results).is_length(2)


def test_strips_ansi_by_default(
    identity_line_parser: Callable[[str], SimpleIssue],
) -> None:
    """Strip ANSI codes by default.

    Args:
        identity_line_parser: Fixture providing identity parser for lines.
    """
    output = "\x1b[31mError\x1b[0m: message\n"
    results = list(stream_text_lines(output, identity_line_parser))

    assert_that(results[0].message).is_equal_to("Error: message")


def test_preserves_ansi_when_disabled(
    identity_line_parser: Callable[[str], SimpleIssue],
) -> None:
    """Preserve ANSI codes when strip_ansi=False.

    Args:
        identity_line_parser: Fixture providing identity parser for lines.
    """
    output = "\x1b[31mError\x1b[0m\n"
    results = list(stream_text_lines(output, identity_line_parser, strip_ansi=False))

    assert_that(results[0].message).contains("\x1b[31m")


def test_skips_empty_lines(
    identity_line_parser: Callable[[str], SimpleIssue],
) -> None:
    """Skip empty lines.

    Args:
        identity_line_parser: Fixture providing identity parser for lines.
    """
    output = "line1\n\n\nline2\n"
    results = list(stream_text_lines(output, identity_line_parser))

    assert_that(results).is_length(2)
