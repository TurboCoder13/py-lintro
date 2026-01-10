"""Unit tests for PlainStyle formatter.

Tests verify PlainStyle correctly formats tabular data as plain text
with proper column alignment and separators.
"""

from __future__ import annotations

from assertpy import assert_that

from lintro.formatters.styles.plain import PlainStyle

from .conftest import MULTI_ROW_DATA, SINGLE_ROW_DATA, STANDARD_COLUMNS, TWO_COLUMNS


def test_plain_style_single_row_contains_all_data(plain_style: PlainStyle) -> None:
    """PlainStyle format includes header and data values.

    Args:
        plain_style: The PlainStyle formatter instance.
    """
    result = plain_style.format(STANDARD_COLUMNS, SINGLE_ROW_DATA)

    assert_that(result).contains("File")
    assert_that(result).contains("src/main.py")
    assert_that(result).contains("Error found")


def test_plain_style_multiple_rows_contains_all_files(
    plain_style: PlainStyle,
) -> None:
    """PlainStyle format includes all file paths from multiple rows.

    Args:
        plain_style: The PlainStyle formatter instance.
    """
    result = plain_style.format(TWO_COLUMNS, MULTI_ROW_DATA)

    assert_that(result).contains("src/a.py")
    assert_that(result).contains("src/b.py")


def test_plain_style_row_shorter_than_columns(plain_style: PlainStyle) -> None:
    """PlainStyle handles row with fewer elements than columns.

    Args:
        plain_style: The PlainStyle formatter instance.
    """
    result = plain_style.format(STANDARD_COLUMNS, [["src/main.py"]])

    assert_that(result).contains("src/main.py")


def test_plain_style_has_separator_line(plain_style: PlainStyle) -> None:
    """PlainStyle output includes separator line with dashes.

    Args:
        plain_style: The PlainStyle formatter instance.
    """
    result = plain_style.format(TWO_COLUMNS, [["src/main.py", "10"]])
    lines = result.split("\n")

    assert_that(len(lines)).is_greater_than_or_equal_to(3)
    assert_that(lines[1]).contains("-")
