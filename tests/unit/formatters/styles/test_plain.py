"""Tests for lintro.formatters.styles.plain module."""

from __future__ import annotations

from assertpy import assert_that

from lintro.formatters.styles.plain import PlainStyle


def test_plain_style_empty_rows(plain_style: PlainStyle) -> None:
    """PlainStyle returns no issues message for empty rows.

    Args:
        plain_style: PlainStyle fixture.
    """
    result = plain_style.format(["File", "Line"], [])
    assert_that(result).is_equal_to("No issues found.")


def test_plain_style_single_row(plain_style: PlainStyle) -> None:
    """PlainStyle formats single row correctly.

    Args:
        plain_style: PlainStyle fixture.
    """
    result = plain_style.format(
        ["File", "Line"],
        [["test.py", "10"]],
    )
    assert_that(result).contains("File | Line")
    assert_that(result).contains("test.py | 10")


def test_plain_style_multiple_rows(plain_style: PlainStyle) -> None:
    """PlainStyle formats multiple rows correctly.

    Args:
        plain_style: PlainStyle fixture.
    """
    result = plain_style.format(
        ["File"],
        [["a.py"], ["b.py"]],
    )
    lines = result.split("\n")
    assert_that(len(lines)).is_equal_to(4)  # header + separator + 2 data


def test_plain_style_has_separator_line(plain_style: PlainStyle) -> None:
    """PlainStyle includes separator line after header.

    Args:
        plain_style: PlainStyle fixture.
    """
    result = plain_style.format(
        ["File", "Line"],
        [["test.py", "10"]],
    )
    lines = result.split("\n")
    # Second line should be dashes
    assert_that(lines[1]).matches(r"^-+$")


def test_plain_style_separator_matches_header_length(
    plain_style: PlainStyle,
) -> None:
    """PlainStyle separator matches header length.

    Args:
        plain_style: PlainStyle fixture.
    """
    result = plain_style.format(
        ["File", "Line"],
        [["test.py", "10"]],
    )
    lines = result.split("\n")
    header_len = len(lines[0])
    separator_len = len(lines[1])
    assert_that(separator_len).is_equal_to(header_len)


def test_plain_style_pads_short_rows(plain_style: PlainStyle) -> None:
    """PlainStyle pads short rows with empty cells.

    Args:
        plain_style: PlainStyle fixture.
    """
    result = plain_style.format(
        ["File", "Line", "Message"],
        [["test.py"]],
    )
    data_line = result.split("\n")[2]
    assert_that(data_line.count("|")).is_equal_to(2)


def test_plain_style_ignores_tool_name(plain_style: PlainStyle) -> None:
    """PlainStyle ignores tool_name parameter.

    Args:
        plain_style: PlainStyle fixture.
    """
    result = plain_style.format(
        ["File"],
        [["test.py"]],
        tool_name="ruff",
    )
    assert_that(result).does_not_contain("ruff")


def test_plain_style_converts_values_to_string(plain_style: PlainStyle) -> None:
    """PlainStyle converts non-string values to strings.

    Args:
        plain_style: PlainStyle fixture.
    """
    result = plain_style.format(
        ["Number", "Bool"],
        [[42, True]],
    )
    assert_that(result).contains("42 | True")
