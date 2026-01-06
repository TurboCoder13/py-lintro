"""Unit tests for the centralized format style registry."""

from assertpy import assert_that

from lintro.enums.output_format import OutputFormat
from lintro.formatters.core.format_registry import (
    DEFAULT_FORMAT,
    get_format_map,
    get_string_format_map,
    get_style,
)
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle


class TestGetStyle:
    """Tests for the get_style function."""

    def test_get_style_with_enum_plain(self) -> None:
        """Test getting PlainStyle with OutputFormat enum."""
        style = get_style(OutputFormat.PLAIN)
        assert_that(style).is_instance_of(PlainStyle)

    def test_get_style_with_enum_grid(self) -> None:
        """Test getting GridStyle with OutputFormat enum."""
        style = get_style(OutputFormat.GRID)
        assert_that(style).is_instance_of(GridStyle)

    def test_get_style_with_enum_markdown(self) -> None:
        """Test getting MarkdownStyle with OutputFormat enum."""
        style = get_style(OutputFormat.MARKDOWN)
        assert_that(style).is_instance_of(MarkdownStyle)

    def test_get_style_with_enum_html(self) -> None:
        """Test getting HtmlStyle with OutputFormat enum."""
        style = get_style(OutputFormat.HTML)
        assert_that(style).is_instance_of(HtmlStyle)

    def test_get_style_with_enum_json(self) -> None:
        """Test getting JsonStyle with OutputFormat enum."""
        style = get_style(OutputFormat.JSON)
        assert_that(style).is_instance_of(JsonStyle)

    def test_get_style_with_enum_csv(self) -> None:
        """Test getting CsvStyle with OutputFormat enum."""
        style = get_style(OutputFormat.CSV)
        assert_that(style).is_instance_of(CsvStyle)

    def test_get_style_with_string_plain(self) -> None:
        """Test getting PlainStyle with string key."""
        style = get_style("plain")
        assert_that(style).is_instance_of(PlainStyle)

    def test_get_style_with_string_grid(self) -> None:
        """Test getting GridStyle with string key."""
        style = get_style("grid")
        assert_that(style).is_instance_of(GridStyle)

    def test_get_style_with_string_markdown(self) -> None:
        """Test getting MarkdownStyle with string key."""
        style = get_style("markdown")
        assert_that(style).is_instance_of(MarkdownStyle)

    def test_get_style_with_string_html(self) -> None:
        """Test getting HtmlStyle with string key."""
        style = get_style("html")
        assert_that(style).is_instance_of(HtmlStyle)

    def test_get_style_with_string_json(self) -> None:
        """Test getting JsonStyle with string key."""
        style = get_style("json")
        assert_that(style).is_instance_of(JsonStyle)

    def test_get_style_with_string_csv(self) -> None:
        """Test getting CsvStyle with string key."""
        style = get_style("csv")
        assert_that(style).is_instance_of(CsvStyle)

    def test_get_style_string_case_insensitive(self) -> None:
        """Test that string keys are case insensitive."""
        style_lower = get_style("grid")
        style_upper = get_style("GRID")
        style_mixed = get_style("Grid")

        assert_that(style_lower).is_instance_of(GridStyle)
        assert_that(style_upper).is_instance_of(GridStyle)
        assert_that(style_mixed).is_instance_of(GridStyle)

    def test_get_style_unknown_string_falls_back_to_grid(self) -> None:
        """Test that unknown format string falls back to GridStyle."""
        style = get_style("unknown_format")
        assert_that(style).is_instance_of(GridStyle)

    def test_get_style_empty_string_falls_back_to_grid(self) -> None:
        """Test that empty string falls back to GridStyle."""
        style = get_style("")
        assert_that(style).is_instance_of(GridStyle)

    def test_styles_are_cached(self) -> None:
        """Test that style instances are cached and reused."""
        style1 = get_style(OutputFormat.GRID)
        style2 = get_style(OutputFormat.GRID)

        # Same instance should be returned (cached)
        assert_that(style1).is_same_as(style2)


class TestGetFormatMap:
    """Tests for the get_format_map function."""

    def test_returns_all_formats(self) -> None:
        """Test that get_format_map returns all output formats."""
        format_map = get_format_map()

        assert_that(format_map).contains_key(OutputFormat.PLAIN)
        assert_that(format_map).contains_key(OutputFormat.GRID)
        assert_that(format_map).contains_key(OutputFormat.MARKDOWN)
        assert_that(format_map).contains_key(OutputFormat.HTML)
        assert_that(format_map).contains_key(OutputFormat.JSON)
        assert_that(format_map).contains_key(OutputFormat.CSV)

    def test_format_map_values_are_styles(self) -> None:
        """Test that format_map values are the correct style types."""
        format_map = get_format_map()

        assert_that(format_map[OutputFormat.PLAIN]).is_instance_of(PlainStyle)
        assert_that(format_map[OutputFormat.GRID]).is_instance_of(GridStyle)
        assert_that(format_map[OutputFormat.MARKDOWN]).is_instance_of(MarkdownStyle)
        assert_that(format_map[OutputFormat.HTML]).is_instance_of(HtmlStyle)
        assert_that(format_map[OutputFormat.JSON]).is_instance_of(JsonStyle)
        assert_that(format_map[OutputFormat.CSV]).is_instance_of(CsvStyle)

    def test_format_map_length(self) -> None:
        """Test that format_map contains exactly 6 formats."""
        format_map = get_format_map()
        assert_that(format_map).is_length(6)


class TestGetStringFormatMap:
    """Tests for the get_string_format_map function."""

    def test_returns_string_keys(self) -> None:
        """Test that get_string_format_map uses string keys."""
        string_map = get_string_format_map()

        assert_that(string_map).contains_key("plain")
        assert_that(string_map).contains_key("grid")
        assert_that(string_map).contains_key("markdown")
        assert_that(string_map).contains_key("html")
        assert_that(string_map).contains_key("json")
        assert_that(string_map).contains_key("csv")

    def test_string_map_values_are_styles(self) -> None:
        """Test that string_map values are the correct style types."""
        string_map = get_string_format_map()

        assert_that(string_map["plain"]).is_instance_of(PlainStyle)
        assert_that(string_map["grid"]).is_instance_of(GridStyle)
        assert_that(string_map["markdown"]).is_instance_of(MarkdownStyle)
        assert_that(string_map["html"]).is_instance_of(HtmlStyle)
        assert_that(string_map["json"]).is_instance_of(JsonStyle)
        assert_that(string_map["csv"]).is_instance_of(CsvStyle)

    def test_string_map_length(self) -> None:
        """Test that string_map contains exactly 6 formats."""
        string_map = get_string_format_map()
        assert_that(string_map).is_length(6)


class TestDefaultFormat:
    """Tests for the DEFAULT_FORMAT constant."""

    def test_default_format_is_grid(self) -> None:
        """Test that the default format is GRID."""
        assert_that(DEFAULT_FORMAT).is_equal_to(OutputFormat.GRID)
