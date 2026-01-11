"""Tests for strip_ansi_codes function."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.base_parser import strip_ansi_codes


def test_strip_ansi_codes_with_color() -> None:
    """Remove ANSI color codes from text."""
    text = "\x1b[31mError\x1b[0m: message"
    result = strip_ansi_codes(text)
    assert_that(result).is_equal_to("Error: message")


def test_strip_ansi_codes_plain_text() -> None:
    """Return plain text unchanged."""
    text = "plain text without codes"
    result = strip_ansi_codes(text)
    assert_that(result).is_equal_to(text)


def test_strip_ansi_codes_multiple_codes() -> None:
    """Remove multiple ANSI codes from text."""
    text = "\x1b[1m\x1b[31mBold Red\x1b[0m normal \x1b[32mgreen\x1b[0m"
    result = strip_ansi_codes(text)
    assert_that(result).is_equal_to("Bold Red normal green")


def test_strip_ansi_codes_empty_string() -> None:
    """Handle empty string input."""
    result = strip_ansi_codes("")
    assert_that(result).is_equal_to("")


def test_strip_ansi_codes_complex_sequences() -> None:
    """Remove complex ANSI sequences with multiple parameters."""
    text = "\x1b[38;5;196mComplex color\x1b[0m"
    result = strip_ansi_codes(text)
    assert_that(result).is_equal_to("Complex color")
