"""Tests for lintro.formatters.styles.html module."""

from __future__ import annotations

from assertpy import assert_that

from lintro.formatters.styles.html import HtmlStyle


def test_html_style_empty_rows(html_style: HtmlStyle) -> None:
    """HtmlStyle returns no issues message for empty rows.

    Args:
        html_style: HtmlStyle fixture.
    """
    result = html_style.format(["File", "Line"], [])
    assert_that(result).is_equal_to("<p>No issues found.</p>")


def test_html_style_single_row(html_style: HtmlStyle) -> None:
    """HtmlStyle formats single row correctly.

    Args:
        html_style: HtmlStyle fixture.
    """
    result = html_style.format(
        ["File", "Line"],
        [["test.py", "10"]],
    )
    assert_that(result).contains("<table>")
    assert_that(result).contains("</table>")
    assert_that(result).contains("<th>File</th>")
    assert_that(result).contains("<td>test.py</td>")


def test_html_style_multiple_rows(html_style: HtmlStyle) -> None:
    """HtmlStyle formats multiple rows correctly.

    Args:
        html_style: HtmlStyle fixture.
    """
    result = html_style.format(
        ["File"],
        [["a.py"], ["b.py"]],
    )
    assert_that(result.count("<tr>")).is_equal_to(3)  # 1 header + 2 data


def test_html_style_escapes_html_characters(html_style: HtmlStyle) -> None:
    """HtmlStyle escapes HTML special characters.

    Args:
        html_style: HtmlStyle fixture.
    """
    result = html_style.format(
        ["Message"],
        [["<script>alert('xss')</script>"]],
    )
    assert_that(result).contains("&lt;script&gt;")
    assert_that(result).does_not_contain("<script>")


def test_html_style_escapes_ampersand(html_style: HtmlStyle) -> None:
    """HtmlStyle escapes ampersand character.

    Args:
        html_style: HtmlStyle fixture.
    """
    result = html_style.format(
        ["Message"],
        [["A & B"]],
    )
    assert_that(result).contains("A &amp; B")


def test_html_style_pads_short_rows(html_style: HtmlStyle) -> None:
    """HtmlStyle pads short rows with empty cells.

    Args:
        html_style: HtmlStyle fixture.
    """
    result = html_style.format(
        ["File", "Line", "Message"],
        [["test.py"]],
    )
    # Should have 3 <td> elements in the row
    assert_that(result.count("<td>")).is_equal_to(3)


def test_html_style_ignores_tool_name(html_style: HtmlStyle) -> None:
    """HtmlStyle ignores tool_name parameter.

    Args:
        html_style: HtmlStyle fixture.
    """
    result = html_style.format(
        ["File"],
        [["test.py"]],
        tool_name="ruff",
    )
    assert_that(result).does_not_contain("ruff")
