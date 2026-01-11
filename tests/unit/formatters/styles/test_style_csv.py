"""Unit tests for CsvStyle formatter.

Tests verify CsvStyle correctly formats tabular data as valid CSV
with proper quoting for special characters.
"""

from __future__ import annotations

from assertpy import assert_that

from lintro.formatters.styles.csv import CsvStyle

from .conftest import MULTI_ROW_DATA, SINGLE_ROW_DATA, STANDARD_COLUMNS, TWO_COLUMNS


def test_csv_style_single_row_produces_valid_csv(csv_style: CsvStyle) -> None:
    """CsvStyle formats single row as valid CSV with header.

    Args:
        csv_style: The CsvStyle formatter instance.
    """
    result = csv_style.format(STANDARD_COLUMNS, SINGLE_ROW_DATA)
    lines = result.strip().split("\n")

    assert_that(lines).is_length(2)  # header + 1 data row
    assert_that(lines[0]).contains("File,Line,Message")
    assert_that(lines[1]).contains("src/main.py,10,Error found")


def test_csv_style_multiple_rows_produces_correct_line_count(
    csv_style: CsvStyle,
) -> None:
    """CsvStyle formats multiple rows with correct number of lines.

    Args:
        csv_style: The CsvStyle formatter instance.
    """
    result = csv_style.format(TWO_COLUMNS, MULTI_ROW_DATA)
    lines = result.strip().split("\n")

    assert_that(lines).is_length(3)  # header + 2 data rows


def test_csv_style_quotes_values_with_commas(csv_style: CsvStyle) -> None:
    """CsvStyle properly quotes values containing commas.

    Args:
        csv_style: The CsvStyle formatter instance.
    """
    result = csv_style.format(["Message"], [["Error, with comma"]])

    assert_that(result).contains('"Error, with comma"')


def test_csv_style_row_shorter_than_columns(csv_style: CsvStyle) -> None:
    """CsvStyle handles row with fewer elements than columns.

    Args:
        csv_style: The CsvStyle formatter instance.
    """
    result = csv_style.format(STANDARD_COLUMNS, [["src/main.py"]])

    assert_that(result).contains("src/main.py")
