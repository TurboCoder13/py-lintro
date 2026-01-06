"""Tests for formatters."""

import pytest
from assertpy import assert_that

from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle

# Test data
SAMPLE_COLUMNS = ["col1", "col2"]
SAMPLE_ROWS = [["val1", "val2"], ["val3", "val4"]]


@pytest.mark.parametrize(
    "style_class,expected_contains",
    [
        (CsvStyle, ["col1,col2", "val1,val2", "val3,val4"]),
        (GridStyle, ["col1", "col2", "val1", "val2"]),
        (HtmlStyle, ["<table>", "<th>col1</th>", "<th>col2</th>", "<td>val1</td>"]),
        (JsonStyle, ["col1", "col2", "val1", "val2"]),
        (MarkdownStyle, ["| col1 | col2 |", "| val1 | val2 |", "| val3 | val4 |"]),
        (PlainStyle, ["col1", "col2", "val1", "val2"]),
    ],
    ids=["csv", "grid", "html", "json", "markdown", "plain"],
)
def test_style_format(style_class: type, expected_contains: list[str]) -> None:
    """Test that each style formats data correctly.

    Args:
        style_class: The formatter style class to test.
        expected_contains: Strings expected in the formatted output.
    """
    style = style_class()
    result = style.format(SAMPLE_COLUMNS, SAMPLE_ROWS)
    assert_that(result).is_instance_of(str)
    assert_that(result).is_not_empty()
    for expected in expected_contains:
        assert_that(result).contains(expected)


@pytest.mark.parametrize(
    "style_class,allows_metadata",
    [
        (CsvStyle, False),
        (GridStyle, False),
        (HtmlStyle, False),
        (JsonStyle, True),  # JSON includes metadata structure even when empty
        (MarkdownStyle, False),
        (PlainStyle, False),
    ],
    ids=["csv", "grid", "html", "json", "markdown", "plain"],
)
def test_style_format_empty(style_class: type, allows_metadata: bool) -> None:
    """Test that all styles handle empty data gracefully.

    Args:
        style_class: The formatter style class to test.
        allows_metadata: Whether the style includes metadata for empty data.
    """
    style = style_class()
    result = style.format([], [])
    assert_that(result).is_instance_of(str)
    if allows_metadata:
        # JSON style produces metadata structure, verify it contains no issues
        assert_that(result).contains('"total_issues": 0')
        assert_that(result).contains('"issues": []')
    else:
        # Other styles should produce empty or minimal output
        assert_that(len(result)).is_less_than_or_equal_to(50)


def test_grid_style_format_fallback() -> None:
    """Test grid style formatting fallback when tabulate is not available."""
    style = GridStyle()
    with pytest.MonkeyPatch().context() as m:
        m.setattr("lintro.formatters.styles.grid.TABULATE_AVAILABLE", False)
        m.setattr("lintro.formatters.styles.grid.tabulate", None)
        result = style.format(SAMPLE_COLUMNS, SAMPLE_ROWS)
        assert_that(result).contains("col1")
        assert_that(result).contains("col2")
        assert_that(result).contains("val1")
        assert_that(result).contains("val2")
        assert_that(result).contains(" | ")


def test_grid_style_format_fallback_empty() -> None:
    """Test grid style formatting fallback with empty data."""
    style = GridStyle()
    with pytest.MonkeyPatch().context() as m:
        m.setattr("lintro.formatters.styles.grid.TABULATE_AVAILABLE", False)
        m.setattr("lintro.formatters.styles.grid.tabulate", None)
        result = style.format([], [])
        assert_that(result).is_equal_to("")


def test_grid_style_format_fallback_single_column() -> None:
    """Test grid style formatting fallback with single column."""
    style = GridStyle()
    with pytest.MonkeyPatch().context() as m:
        m.setattr("lintro.formatters.styles.grid.TABULATE_AVAILABLE", False)
        m.setattr("lintro.formatters.styles.grid.tabulate", None)
        result = style.format(["col1"], [["val1"], ["val2"]])
        assert_that(result).contains("col1")
        assert_that(result).contains("val1")
        assert_that(result).contains("val2")
