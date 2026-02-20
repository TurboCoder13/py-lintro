"""Unit tests for the centralized format style registry."""

import pytest
from assertpy import assert_that

from lintro.enums.output_format import OutputFormat
from lintro.formatters.core.format_registry import (
    DEFAULT_FORMAT,
    get_format_map,
    get_string_format_map,
    get_style,
)
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.github import GitHubStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle

# =============================================================================
# Tests for get_style function
# =============================================================================


@pytest.mark.parametrize(
    ("output_format", "expected_style"),
    [
        pytest.param(OutputFormat.PLAIN, PlainStyle, id="enum-plain"),
        pytest.param(OutputFormat.GRID, GridStyle, id="enum-grid"),
        pytest.param(OutputFormat.MARKDOWN, MarkdownStyle, id="enum-markdown"),
        pytest.param(OutputFormat.HTML, HtmlStyle, id="enum-html"),
        pytest.param(OutputFormat.JSON, JsonStyle, id="enum-json"),
        pytest.param(OutputFormat.CSV, CsvStyle, id="enum-csv"),
        pytest.param(OutputFormat.GITHUB, GitHubStyle, id="enum-github"),
    ],
)
def test_get_style_with_enum(output_format: OutputFormat, expected_style: type) -> None:
    """Test getting style with OutputFormat enum.

    Args:
        output_format: The OutputFormat enum value to test.
        expected_style: The expected style class type.
    """
    style = get_style(output_format)
    assert_that(style).is_instance_of(expected_style)


@pytest.mark.parametrize(
    ("format_string", "expected_style"),
    [
        pytest.param("plain", PlainStyle, id="string-plain"),
        pytest.param("grid", GridStyle, id="string-grid"),
        pytest.param("markdown", MarkdownStyle, id="string-markdown"),
        pytest.param("html", HtmlStyle, id="string-html"),
        pytest.param("json", JsonStyle, id="string-json"),
        pytest.param("csv", CsvStyle, id="string-csv"),
        pytest.param("github", GitHubStyle, id="string-github"),
    ],
)
def test_get_style_with_string(format_string: str, expected_style: type) -> None:
    """Test getting style with string key.

    Args:
        format_string: The string format key to test.
        expected_style: The expected style class type.
    """
    style = get_style(format_string)
    assert_that(style).is_instance_of(expected_style)


@pytest.mark.parametrize(
    "format_string",
    [
        pytest.param("grid", id="lowercase"),
        pytest.param("GRID", id="uppercase"),
        pytest.param("Grid", id="mixed-case"),
    ],
)
def test_get_style_string_case_insensitive(format_string: str) -> None:
    """Test that string keys are case insensitive.

    Args:
        format_string: The format string with varying case to test.
    """
    style = get_style(format_string)
    assert_that(style).is_instance_of(GridStyle)


@pytest.mark.parametrize(
    "format_string",
    [
        pytest.param("unknown_format", id="unknown"),
        pytest.param("", id="empty"),
    ],
)
def test_get_style_unknown_format_falls_back_to_grid(format_string: str) -> None:
    """Test that unknown or empty format string falls back to GridStyle.

    Args:
        format_string: The unknown or empty format string to test.
    """
    style = get_style(format_string)
    assert_that(style).is_instance_of(GridStyle)


def test_get_style_caches_instances() -> None:
    """Test that style instances are cached and reused."""
    style1 = get_style(OutputFormat.GRID)
    style2 = get_style(OutputFormat.GRID)

    # Same instance should be returned (cached)
    assert_that(style1).is_same_as(style2)


# =============================================================================
# Tests for get_format_map function
# =============================================================================


def test_get_format_map_returns_all_formats() -> None:
    """Test that get_format_map returns all output formats."""
    format_map = get_format_map()

    assert_that(format_map).contains_key(OutputFormat.PLAIN)
    assert_that(format_map).contains_key(OutputFormat.GRID)
    assert_that(format_map).contains_key(OutputFormat.MARKDOWN)
    assert_that(format_map).contains_key(OutputFormat.HTML)
    assert_that(format_map).contains_key(OutputFormat.JSON)
    assert_that(format_map).contains_key(OutputFormat.CSV)
    assert_that(format_map).contains_key(OutputFormat.GITHUB)


def test_get_format_map_values_are_correct_styles() -> None:
    """Test that format_map values are the correct style types."""
    format_map = get_format_map()

    assert_that(format_map[OutputFormat.PLAIN]).is_instance_of(PlainStyle)
    assert_that(format_map[OutputFormat.GRID]).is_instance_of(GridStyle)
    assert_that(format_map[OutputFormat.MARKDOWN]).is_instance_of(MarkdownStyle)
    assert_that(format_map[OutputFormat.HTML]).is_instance_of(HtmlStyle)
    assert_that(format_map[OutputFormat.JSON]).is_instance_of(JsonStyle)
    assert_that(format_map[OutputFormat.CSV]).is_instance_of(CsvStyle)
    assert_that(format_map[OutputFormat.GITHUB]).is_instance_of(GitHubStyle)


def test_get_format_map_length() -> None:
    """Test that format_map contains exactly 7 formats."""
    format_map = get_format_map()
    assert_that(format_map).is_length(7)


# =============================================================================
# Tests for get_string_format_map function
# =============================================================================


def test_get_string_format_map_returns_string_keys() -> None:
    """Test that get_string_format_map uses string keys."""
    string_map = get_string_format_map()

    assert_that(string_map).contains_key("plain")
    assert_that(string_map).contains_key("grid")
    assert_that(string_map).contains_key("markdown")
    assert_that(string_map).contains_key("html")
    assert_that(string_map).contains_key("json")
    assert_that(string_map).contains_key("csv")
    assert_that(string_map).contains_key("github")


def test_get_string_format_map_values_are_correct_styles() -> None:
    """Test that string_map values are the correct style types."""
    string_map = get_string_format_map()

    assert_that(string_map["plain"]).is_instance_of(PlainStyle)
    assert_that(string_map["grid"]).is_instance_of(GridStyle)
    assert_that(string_map["markdown"]).is_instance_of(MarkdownStyle)
    assert_that(string_map["html"]).is_instance_of(HtmlStyle)
    assert_that(string_map["json"]).is_instance_of(JsonStyle)
    assert_that(string_map["csv"]).is_instance_of(CsvStyle)
    assert_that(string_map["github"]).is_instance_of(GitHubStyle)


def test_get_string_format_map_length() -> None:
    """Test that string_map contains exactly 7 formats."""
    string_map = get_string_format_map()
    assert_that(string_map).is_length(7)


# =============================================================================
# Tests for DEFAULT_FORMAT constant
# =============================================================================


def test_default_format_is_grid() -> None:
    """Test that the default format is GRID."""
    assert_that(DEFAULT_FORMAT).is_equal_to(OutputFormat.GRID)
