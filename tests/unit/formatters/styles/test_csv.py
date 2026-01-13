"""Tests for lintro.formatters.styles.csv module."""

from __future__ import annotations

from assertpy import assert_that

from lintro.formatters.styles.csv import CsvStyle


def test_csv_style_empty_rows(csv_style: CsvStyle) -> None:
    """CsvStyle returns empty string for empty rows.

    Args:
        csv_style: CsvStyle fixture.
    """
    result = csv_style.format(["File", "Line"], [])
    assert_that(result).is_equal_to("")


def test_csv_style_single_row(csv_style: CsvStyle) -> None:
    """CsvStyle formats single row correctly.

    Args:
        csv_style: CsvStyle fixture.
    """
    result = csv_style.format(
        ["File", "Line", "Message"],
        [["test.py", "10", "Error"]],
    )
    assert_that(result).contains("File,Line,Message")
    assert_that(result).contains("test.py,10,Error")


def test_csv_style_multiple_rows(csv_style: CsvStyle) -> None:
    """CsvStyle formats multiple rows correctly.

    Args:
        csv_style: CsvStyle fixture.
    """
    result = csv_style.format(
        ["File", "Line"],
        [["a.py", "1"], ["b.py", "2"]],
    )
    lines = result.strip().split("\n")
    assert_that(len(lines)).is_equal_to(3)  # header + 2 data rows


def test_csv_style_pads_short_rows(csv_style: CsvStyle) -> None:
    """CsvStyle pads short rows with empty strings.

    Args:
        csv_style: CsvStyle fixture.
    """
    result = csv_style.format(
        ["File", "Line", "Message"],
        [["test.py"]],
    )
    assert_that(result).contains("test.py,,")


def test_csv_style_escapes_special_characters(csv_style: CsvStyle) -> None:
    """CsvStyle escapes special CSV characters.

    Args:
        csv_style: CsvStyle fixture.
    """
    result = csv_style.format(
        ["Message"],
        [["Value with, comma"]],
    )
    # CSV writer should quote fields containing commas
    assert_that(result).contains('"Value with, comma"')


def test_csv_style_ignores_tool_name(csv_style: CsvStyle) -> None:
    """CsvStyle ignores tool_name parameter.

    Args:
        csv_style: CsvStyle fixture.
    """
    result = csv_style.format(
        ["File"],
        [["test.py"]],
        tool_name="ruff",
    )
    assert_that(result).does_not_contain("ruff")


def test_csv_style_ignores_kwargs(csv_style: CsvStyle) -> None:
    """CsvStyle ignores extra kwargs.

    Args:
        csv_style: CsvStyle fixture.
    """
    result = csv_style.format(
        ["File"],
        [["test.py"]],
        extra_param="ignored",
    )
    assert_that(result).contains("test.py")
