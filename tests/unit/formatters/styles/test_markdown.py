"""Tests for lintro.formatters.styles.markdown module."""

from __future__ import annotations

from assertpy import assert_that

from lintro.formatters.styles.markdown import MarkdownStyle


def test_markdown_style_empty_rows(markdown_style: MarkdownStyle) -> None:
    """MarkdownStyle returns no issues message for empty rows.

    Args:
        markdown_style: MarkdownStyle fixture.
    """
    result = markdown_style.format(["File", "Line"], [])
    assert_that(result).is_equal_to("No issues found.")


def test_markdown_style_single_row(markdown_style: MarkdownStyle) -> None:
    """MarkdownStyle formats single row correctly.

    Args:
        markdown_style: MarkdownStyle fixture.
    """
    result = markdown_style.format(
        ["File", "Line"],
        [["test.py", "10"]],
    )
    assert_that(result).contains("| File | Line |")
    assert_that(result).contains("| --- | --- |")
    assert_that(result).contains("| test.py | 10 |")


def test_markdown_style_multiple_rows(markdown_style: MarkdownStyle) -> None:
    """MarkdownStyle formats multiple rows correctly.

    Args:
        markdown_style: MarkdownStyle fixture.
    """
    result = markdown_style.format(
        ["File"],
        [["a.py"], ["b.py"]],
    )
    lines = result.split("\n")
    assert_that(len(lines)).is_equal_to(4)  # header + separator + 2 data


def test_markdown_style_escapes_pipe_character(markdown_style: MarkdownStyle) -> None:
    """MarkdownStyle escapes pipe characters in content.

    Args:
        markdown_style: MarkdownStyle fixture.
    """
    result = markdown_style.format(
        ["Message"],
        [["A | B"]],
    )
    assert_that(result).contains("A \\| B")


def test_markdown_style_pads_short_rows(markdown_style: MarkdownStyle) -> None:
    """MarkdownStyle pads short rows with empty cells.

    Args:
        markdown_style: MarkdownStyle fixture.
    """
    result = markdown_style.format(
        ["File", "Line", "Message"],
        [["test.py"]],
    )
    # Row should have 3 cells separated by |
    data_line = result.split("\n")[2]
    assert_that(data_line.count("|")).is_equal_to(4)  # leading + 3 separators


def test_markdown_style_ignores_tool_name(markdown_style: MarkdownStyle) -> None:
    """MarkdownStyle ignores tool_name parameter.

    Args:
        markdown_style: MarkdownStyle fixture.
    """
    result = markdown_style.format(
        ["File"],
        [["test.py"]],
        tool_name="ruff",
    )
    assert_that(result).does_not_contain("ruff")


def test_markdown_style_separator_matches_columns(
    markdown_style: MarkdownStyle,
) -> None:
    """MarkdownStyle separator row matches column count.

    Args:
        markdown_style: MarkdownStyle fixture.
    """
    result = markdown_style.format(
        ["A", "B", "C", "D"],
        [["1", "2", "3", "4"]],
    )
    separator_line = result.split("\n")[1]
    assert_that(separator_line.count("---")).is_equal_to(4)
