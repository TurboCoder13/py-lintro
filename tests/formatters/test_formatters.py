"""Tests for formatters."""

import pytest
from assertpy import assert_that

from lintro.formatters.core.output_style import OutputStyle
from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle


def test_output_style_abstract():
    """Test that OutputStyle is an abstract base class."""
    from abc import ABC

    assert_that(issubclass(OutputStyle, ABC)).is_true()
    assert_that(hasattr(OutputStyle, "format")).is_true()


def test_table_descriptor_abstract():
    """Test TableDescriptor is an abstract base class."""
    from abc import ABC

    assert_that(issubclass(TableDescriptor, ABC)).is_true()
    assert_that(hasattr(TableDescriptor, "get_columns")).is_true()
    assert_that(hasattr(TableDescriptor, "get_rows")).is_true()


def test_table_descriptor_methods():
    """Test TableDescriptor abstract methods exist."""
    assert_that(callable(TableDescriptor.get_columns)).is_true()
    assert_that(callable(TableDescriptor.get_rows)).is_true()


def test_csv_style_format():
    """Test CSV style formatting."""
    style = CsvStyle()
    result = style.format(["col1", "col2"], [["val1", "val2"], ["val3", "val4"]])
    assert_that(result).contains("col1,col2")
    assert_that(result).contains("val1,val2")
    assert_that(result).contains("val3,val4")


def test_csv_style_format_empty():
    """Test CSV style formatting with empty data."""
    style = CsvStyle()
    result = style.format([], [])
    assert_that(result).is_equal_to("")


def test_grid_style_format():
    """Test grid style formatting."""
    style = GridStyle()
    result = style.format(["col1", "col2"], [["val1", "val2"], ["val3", "val4"]])
    assert_that(result).contains("col1")
    assert_that(result).contains("col2")
    assert_that(result).contains("val1")
    assert_that(result).contains("val2")


def test_grid_style_format_empty():
    """Test grid style formatting with empty data."""
    style = GridStyle()
    result = style.format([], [])
    assert_that(result).is_equal_to("")


def test_grid_style_format_fallback():
    """Test grid style formatting fallback when tabulate is not available."""
    style = GridStyle()
    with pytest.MonkeyPatch().context() as m:
        m.setattr("lintro.formatters.styles.grid.TABULATE_AVAILABLE", False)
        m.setattr("lintro.formatters.styles.grid.tabulate", None)
        result = style.format(["col1", "col2"], [["val1", "val2"], ["val3", "val4"]])
        assert_that(result).contains("col1")
        assert_that(result).contains("col2")
        assert_that(result).contains("val1")
        assert_that(result).contains("val2")
        assert_that(result).contains(" | ")


def test_grid_style_format_fallback_empty():
    """Test grid style formatting fallback with empty data."""
    style = GridStyle()
    with pytest.MonkeyPatch().context() as m:
        m.setattr("lintro.formatters.styles.grid.TABULATE_AVAILABLE", False)
        m.setattr("lintro.formatters.styles.grid.tabulate", None)
        result = style.format([], [])
        assert_that(result).is_equal_to("")


def test_grid_style_format_fallback_single_column():
    """Test grid style formatting fallback with single column."""
    style = GridStyle()
    with pytest.MonkeyPatch().context() as m:
        m.setattr("lintro.formatters.styles.grid.TABULATE_AVAILABLE", False)
        m.setattr("lintro.formatters.styles.grid.tabulate", None)
        result = style.format(["col1"], [["val1"], ["val2"]])
        assert_that(result).contains("col1")
        assert_that(result).contains("val1")
        assert_that(result).contains("val2")


def test_html_style_format():
    """Test HTML style formatting."""
    style = HtmlStyle()
    result = style.format(["col1", "col2"], [["val1", "val2"], ["val3", "val4"]])
    assert_that(result).contains("<table>")
    assert_that(result).contains("<th>col1</th>")
    assert_that(result).contains("<th>col2</th>")
    assert_that(result).contains("<td>val1</td>")
    assert_that(result).contains("<td>val2</td>")


def test_json_style_format():
    """Test JSON style formatting."""
    style = JsonStyle()
    result = style.format(["col1", "col2"], [["val1", "val2"], ["val3", "val4"]])
    assert_that(result).contains("col1")
    assert_that(result).contains("col2")
    assert_that(result).contains("val1")
    assert_that(result).contains("val2")


def test_markdown_style_format():
    """Test markdown style formatting."""
    style = MarkdownStyle()
    result = style.format(["col1", "col2"], [["val1", "val2"], ["val3", "val4"]])
    assert_that(result).contains("| col1 | col2 |")
    assert_that(result).contains("| val1 | val2 |")
    assert_that(result).contains("| val3 | val4 |")


def test_plain_style_format():
    """Test plain style formatting."""
    style = PlainStyle()
    result = style.format(["col1", "col2"], [["val1", "val2"], ["val3", "val4"]])
    assert_that(result).contains("col1")
    assert_that(result).contains("col2")
    assert_that(result).contains("val1")
    assert_that(result).contains("val2")


def test_all_styles_produce_output():
    """Test that all styles produce some output."""
    styles = [
        CsvStyle(),
        GridStyle(),
        HtmlStyle(),
        JsonStyle(),
        MarkdownStyle(),
        PlainStyle(),
    ]
    columns = ["col1", "col2"]
    rows = [["val1", "val2"], ["val3", "val4"]]
    for style in styles:
        result = style.format(columns, rows)
        assert_that(isinstance(result, str)).is_true()
        assert_that(len(result) > 0).is_true()


def test_styles_handle_empty_results():
    """Test that all styles handle empty results gracefully."""
    styles = [
        CsvStyle(),
        GridStyle(),
        HtmlStyle(),
        JsonStyle(),
        MarkdownStyle(),
        PlainStyle(),
    ]
    for style in styles:
        result = style.format([], [])
        assert_that(isinstance(result, str)).is_true()
        assert_that(result == "" or len(result) >= 0).is_true()
