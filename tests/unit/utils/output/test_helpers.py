"""Tests for lintro.utils.output.helpers module."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.utils.output.helpers import html_escape, markdown_escape, sanitize_csv_value

# =============================================================================
# markdown_escape tests
# =============================================================================


def test_markdown_escape_escapes_pipe() -> None:
    """markdown_escape escapes pipe characters."""
    result = markdown_escape("A | B")
    assert_that(result).is_equal_to(r"A \| B")


def test_markdown_escape_replaces_newline_with_space() -> None:
    """markdown_escape replaces newlines with spaces."""
    result = markdown_escape("line1\nline2")
    assert_that(result).is_equal_to("line1 line2")


def test_markdown_escape_handles_multiple_pipes() -> None:
    """markdown_escape handles multiple pipe characters."""
    result = markdown_escape("A | B | C")
    assert_that(result).is_equal_to(r"A \| B \| C")


def test_markdown_escape_handles_multiple_newlines() -> None:
    """markdown_escape handles multiple newlines."""
    result = markdown_escape("a\nb\nc")
    assert_that(result).is_equal_to("a b c")


def test_markdown_escape_handles_empty_string() -> None:
    """markdown_escape returns empty string for empty input."""
    result = markdown_escape("")
    assert_that(result).is_equal_to("")


def test_markdown_escape_no_change_for_normal_text() -> None:
    """markdown_escape returns unchanged text without special chars."""
    result = markdown_escape("normal text")
    assert_that(result).is_equal_to("normal text")


# =============================================================================
# html_escape tests
# =============================================================================


def test_html_escape_escapes_less_than() -> None:
    """html_escape escapes less than character."""
    result = html_escape("<script>")
    assert_that(result).is_equal_to("&lt;script&gt;")


def test_html_escape_escapes_greater_than() -> None:
    """html_escape escapes greater than character."""
    result = html_escape("a > b")
    assert_that(result).is_equal_to("a &gt; b")


def test_html_escape_escapes_ampersand() -> None:
    """html_escape escapes ampersand character."""
    result = html_escape("A & B")
    assert_that(result).is_equal_to("A &amp; B")


def test_html_escape_escapes_quotes() -> None:
    """html_escape escapes quote characters."""
    result = html_escape('say "hello"')
    assert_that(result).is_equal_to("say &quot;hello&quot;")


def test_html_escape_handles_empty_string() -> None:
    """html_escape returns empty string for empty input."""
    result = html_escape("")
    assert_that(result).is_equal_to("")


def test_html_escape_no_change_for_normal_text() -> None:
    """html_escape returns unchanged text without special chars."""
    result = html_escape("normal text")
    assert_that(result).is_equal_to("normal text")


# =============================================================================
# sanitize_csv_value tests
# =============================================================================


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        pytest.param("=SUM(A1)", "'=SUM(A1)", id="equals_sign"),
        pytest.param("+1234", "'+1234", id="plus_sign"),
        pytest.param("-5678", "'-5678", id="minus_sign"),
        pytest.param("@mention", "'@mention", id="at_sign"),
    ],
)
def test_sanitize_csv_value_prefixes_formula_chars(
    input_value: str,
    expected: str,
) -> None:
    """sanitize_csv_value prefixes formula-starting characters with quote.

    Args:
        input_value: Input value to sanitize.
        expected: Expected sanitized output.
    """
    result = sanitize_csv_value(input_value)
    assert_that(result).is_equal_to(expected)


def test_sanitize_csv_value_no_change_for_normal_text() -> None:
    """sanitize_csv_value returns unchanged text without formula chars."""
    result = sanitize_csv_value("normal text")
    assert_that(result).is_equal_to("normal text")


def test_sanitize_csv_value_handles_empty_string() -> None:
    """sanitize_csv_value returns empty string for empty input."""
    result = sanitize_csv_value("")
    assert_that(result).is_equal_to("")


def test_sanitize_csv_value_does_not_prefix_middle_chars() -> None:
    """sanitize_csv_value only checks start of string."""
    result = sanitize_csv_value("a=b+c-d@e")
    assert_that(result).is_equal_to("a=b+c-d@e")
