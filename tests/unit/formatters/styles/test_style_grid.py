"""Unit tests for GridStyle formatter.

Tests verify GridStyle correctly formats tabular data as grid-style
tables with borders and proper alignment.
"""

from __future__ import annotations

from assertpy import assert_that

from lintro.formatters.styles.grid import GridStyle

from .conftest import MULTI_ROW_DATA, SINGLE_ROW_DATA, STANDARD_COLUMNS, TWO_COLUMNS


def test_grid_style_single_row_contains_header_and_data(
    grid_style: GridStyle,
) -> None:
    """GridStyle format includes header and data values.

    Args:
        grid_style: The GridStyle formatter instance.
    """
    result = grid_style.format(STANDARD_COLUMNS, SINGLE_ROW_DATA)

    assert_that(result).contains("File")
    assert_that(result).contains("src/main.py")


def test_grid_style_multiple_rows_contains_all_files(grid_style: GridStyle) -> None:
    """GridStyle format includes all file paths from multiple rows.

    Args:
        grid_style: The GridStyle formatter instance.
    """
    result = grid_style.format(TWO_COLUMNS, MULTI_ROW_DATA)

    assert_that(result).contains("src/a.py")
    assert_that(result).contains("src/b.py")


def test_grid_style_column_alignment_produces_output(grid_style: GridStyle) -> None:
    """GridStyle with alignment columns produces non-empty formatted output.

    Args:
        grid_style: The GridStyle formatter instance.
    """
    result = grid_style.format(
        ["File", "Line", "Column", "Fixable"],
        [["src/main.py", "10", "5", "Yes"]],
    )

    assert_that(result).is_not_empty()


def test_grid_style_empty_columns_handles_gracefully(grid_style: GridStyle) -> None:
    """GridStyle handles empty columns list without error.

    Args:
        grid_style: The GridStyle formatter instance.
    """
    result = grid_style.format([], [["data"]])

    assert_that(result).is_not_none()
