"""Tests for the formatters module.

This module contains tests for the formatter utilities in Lintro.
"""

import pytest
import json

from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.models.core.tool_result import ToolResult
from lintro.models.core.tool import Tool


@pytest.fixture
def sample_tool_results():
    """Provide sample tool results for testing.

    Returns:
        list[ToolResult]: List of sample ToolResult objects.
    """
    tool1 = Tool(name="ruff", priority=1)
    tool2 = Tool(name="yamllint", priority=2)

    result1 = ToolResult(
        tool=tool1,
        success=True,
        issues=[],
        raw_output="",
        error_message="",
    )
    result2 = ToolResult(
        tool=tool2,
        success=False,
        issues=[
            {"file": "test.py", "line": 1, "message": "Error 1"},
            {"file": "test.py", "line": 5, "message": "Error 2"},
        ],
        raw_output="",
        error_message="",
    )

    return [result1, result2]


def test_output_style_values():
    """Test that supported output styles are available via FORMAT_MAP."""
    from lintro.formatters.tools.darglint_formatter import FORMAT_MAP as DARG_FMT

    expected = {"plain", "grid", "markdown", "html", "json", "csv"}
    assert set(DARG_FMT.keys()) == expected


def test_table_descriptor_creation():
    """Test creating a DarglintTableDescriptor."""
    from lintro.formatters.tools.darglint_formatter import DarglintTableDescriptor

    descriptor = DarglintTableDescriptor()
    assert descriptor.get_columns() == ["File", "Line", "Code", "Message"]

    # Provide a fake issue object with required attributes
    class FakeIssue:
        file = "foo.py"
        line = 1
        code = "D100"
        message = "Missing docstring"

    issues = [FakeIssue()]
    rows = descriptor.get_rows(issues)
    assert rows == [["foo.py", "1", "D100", "Missing docstring"]]


def test_table_descriptor_empty():
    """Test DarglintTableDescriptor with empty issues."""
    from lintro.formatters.tools.darglint_formatter import DarglintTableDescriptor

    descriptor = DarglintTableDescriptor()
    rows = descriptor.get_rows([])
    assert rows == []


@pytest.mark.formatters
def test_csv_style_format():
    """Test CSV style formatting."""
    formatter = CsvStyle()
    columns = ["Tool", "Status", "Issues"]
    rows = [["ruff", "Success", "0"], ["yamllint", "Failed", "2"]]

    result = formatter.format(columns, rows)

    assert isinstance(result, str)
    assert "," in result
    assert "ruff" in result
    assert "yamllint" in result


@pytest.mark.formatters
def test_csv_style_format_empty():
    """Test CSV style with empty rows."""
    formatter = CsvStyle()
    result = formatter.format(["Header1", "Header2"], [])

    assert isinstance(result, str)
    assert result == ""


@pytest.mark.formatters
def test_grid_style_format():
    """Test Grid style formatting."""
    formatter = GridStyle()
    columns = ["Tool", "Status", "Issues"]
    rows = [["ruff", "Success", "0"], ["yamllint", "Failed", "2"]]

    result = formatter.format(columns, rows)

    assert isinstance(result, str)
    assert "ruff" in result
    assert "yamllint" in result


@pytest.mark.formatters
def test_html_style_format():
    """Test HTML style formatting."""
    formatter = HtmlStyle()
    columns = ["Tool", "Status", "Issues"]
    rows = [["ruff", "Success", "0"], ["yamllint", "Failed", "2"]]

    result = formatter.format(columns, rows)

    assert isinstance(result, str)
    assert "<table>" in result
    assert "ruff" in result
    assert "yamllint" in result


@pytest.mark.formatters
def test_json_style_format():
    """Test JSON style formatting."""
    formatter = JsonStyle()
    columns = ["Tool", "Status", "Issues"]
    rows = [["ruff", "Success", "0"], ["yamllint", "Failed", "2"]]

    result = formatter.format(columns, rows)

    assert isinstance(result, str)
    assert "ruff" in result
    assert "yamllint" in result

    # Should be valid JSON
    parsed = json.loads(result)
    assert isinstance(parsed, dict)


@pytest.mark.formatters
def test_markdown_style_format():
    """Test Markdown style formatting."""
    formatter = MarkdownStyle()
    columns = ["Tool", "Status", "Issues"]
    rows = [["ruff", "Success", "0"], ["yamllint", "Failed", "2"]]

    result = formatter.format(columns, rows)

    assert isinstance(result, str)
    assert "|" in result
    assert "ruff" in result
    assert "yamllint" in result


@pytest.mark.formatters
def test_plain_style_format():
    """Test Plain style formatting."""
    formatter = PlainStyle()
    columns = ["Tool", "Status", "Issues"]
    rows = [["ruff", "Success", "0"], ["yamllint", "Failed", "2"]]

    result = formatter.format(columns, rows)

    assert isinstance(result, str)
    assert "ruff" in result
    assert "yamllint" in result


@pytest.mark.formatters
def test_all_styles_produce_output():
    """Test that all styles produce some output."""
    formatters = [
        CsvStyle(),
        GridStyle(),
        HtmlStyle(),
        JsonStyle(),
        MarkdownStyle(),
        PlainStyle(),
    ]

    columns = ["Tool", "Status"]
    rows = [["ruff", "Success"]]

    for formatter in formatters:
        result = formatter.format(columns, rows)
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.formatters
def test_styles_handle_empty_results():
    """Test that all styles handle empty results gracefully."""
    formatters = [
        CsvStyle(),
        GridStyle(),
        HtmlStyle(),
        JsonStyle(),
        MarkdownStyle(),
        PlainStyle(),
    ]

    for formatter in formatters:
        result = formatter.format([], [])
        assert isinstance(result, str)
        # Should not raise any exceptions
