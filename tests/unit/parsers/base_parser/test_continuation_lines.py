"""Tests for collect_continuation_lines function."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.base_parser import collect_continuation_lines


def test_collect_continuation_lines_with_indented_lines() -> None:
    """Collect indented continuation lines."""
    lines = ["main message", "    continued", "    more", "next item"]
    message, next_idx = collect_continuation_lines(
        lines,
        1,
        lambda line: line.startswith("    "),
    )
    assert_that(message).is_equal_to("continued more")
    assert_that(next_idx).is_equal_to(3)


def test_collect_continuation_lines_with_colon_prefix() -> None:
    """Collect lines with colon prefix."""
    lines = ["error:", ": detail1", ": detail2", "next"]
    message, next_idx = collect_continuation_lines(
        lines,
        1,
        lambda line: line.strip().startswith(":"),
    )
    assert_that(message).is_equal_to("detail1 detail2")
    assert_that(next_idx).is_equal_to(3)


def test_collect_continuation_lines_no_continuations() -> None:
    """Return empty message when no continuation lines found."""
    lines = ["main message", "not indented"]
    message, next_idx = collect_continuation_lines(
        lines,
        1,
        lambda line: line.startswith("    "),
    )
    assert_that(message).is_equal_to("")
    assert_that(next_idx).is_equal_to(1)


def test_collect_continuation_lines_at_end() -> None:
    """Handle continuation at end of lines list."""
    lines = ["main", "    last"]
    message, next_idx = collect_continuation_lines(
        lines,
        1,
        lambda line: line.startswith("    "),
    )
    assert_that(message).is_equal_to("last")
    assert_that(next_idx).is_equal_to(2)


def test_collect_continuation_lines_empty_continuation() -> None:
    """Skip empty continuation lines."""
    lines = ["main", "    ", "    content"]
    message, next_idx = collect_continuation_lines(
        lines,
        1,
        lambda line: line.startswith("    "),
    )
    assert_that(message).is_equal_to("content")
    assert_that(next_idx).is_equal_to(3)
