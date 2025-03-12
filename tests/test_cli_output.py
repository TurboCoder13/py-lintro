"""Tests for Lintro CLI output formatting."""

import pytest
from unittest.mock import patch, MagicMock

from lintro.cli import (
    count_issues,
    format_tool_output,
    print_tool_header,
    print_tool_footer,
    print_summary,
    ToolResult,
)


def test_count_issues_black():
    """Test counting issues in Black output."""
    output = """
would reformat file1.py
would reformat file2.py
would reformat file3.py

Oh no! 💥 💔 💥
3 files would be reformatted.
"""
    assert count_issues(output, "black") == 3


def test_count_issues_isort():
    """Test counting issues in isort output."""
    output = """
ERROR: file1.py Imports are incorrectly sorted.
ERROR: file2.py Imports are incorrectly sorted.
Skipped 2 files
"""
    assert count_issues(output, "isort") == 2


def test_count_issues_flake8():
    """Test counting issues in flake8 output."""
    output = """
file1.py:10:1: E302 expected 2 blank lines, found 1
file1.py:15:5: E303 too many blank lines (2)
file2.py:5:80: E501 line too long (100 > 88 characters)
"""
    assert count_issues(output, "flake8") == 3


def test_count_issues_generic():
    """Test counting issues in generic output."""
    output = """
Found 2 errors and 3 warnings.
There are some problems with your code.
"""
    assert count_issues(output, "generic") == 3


@patch("click.secho")
def test_print_tool_header(
    mock_secho
):
    """Test printing a tool header."""
    print_tool_header("test-tool", "check")
    assert mock_secho.call_count == 3
    # Check that the tool name and action are in the second call
    assert "test-tool" in mock_secho.call_args_list[1][0][0]
    assert "check" in mock_secho.call_args_list[1][0][0]


@patch("click.secho")
def test_print_tool_footer_success(
    mock_secho
):
    """Test printing a tool footer for success."""
    print_tool_footer(True, 0)
    assert mock_secho.call_count == 2
    # Check that "No issues found" is in the first call
    assert "No issues found" in mock_secho.call_args_list[0][0][0]
    # Check that the color is green
    assert mock_secho.call_args_list[0][1]["fg"] == "green"


@patch("click.secho")
def test_print_tool_footer_failure(
    mock_secho
):
    """Test printing a tool footer for failure."""
    print_tool_footer(False, 5)
    assert mock_secho.call_count == 2
    # Check that "Found 5 issues" is in the first call
    assert "Found 5 issues" in mock_secho.call_args_list[0][0][0]
    # Check that the color is red
    assert mock_secho.call_args_list[0][1]["fg"] == "red"


@patch("click.secho")
@patch("click.echo")
def test_print_summary(
    mock_echo,
    mock_secho,
):
    """Test printing a summary of tool results."""
    results = [
        ToolResult(name="tool1", success=True, output="output1", issues_count=0),
        ToolResult(name="tool2", success=False, output="output2", issues_count=3),
        ToolResult(name="tool3", success=False, output="output3", issues_count=2),
    ]

    print_summary(results, "check")

    # Check that the summary header is printed
    assert any("Summary (check)" in call[0][0] for call in mock_secho.call_args_list)
    
    # Check that each tool is printed with its status
    assert mock_echo.call_count >= 3  # At least one call per tool
    
    # Check total issues
    assert any("Total: " in call[0][0] and "5 issues" in call[0][0] for call in mock_echo.call_args_list)


@patch("click.style")
def test_format_tool_output_black(mock_style):
    """Test formatting Black output."""
    mock_style.side_effect = lambda text, **kwargs: f"STYLED({text})"

    output = """
would reformat file1.py
would reformat file2.py

Oh no! 💥 💔 💥
2 files would be reformatted.
"""

    formatted = format_tool_output(output.strip(), "black")

    # Check that file paths are styled
    assert "STYLED(- file1.py" in formatted
    assert "STYLED(- file2.py" in formatted
    assert "formatting required" in formatted
    assert "STYLED(Oh no! 💥 💔 💥)" in formatted


@patch("click.style")
def test_format_tool_output_isort(mock_style):
    """Test formatting isort output."""
    mock_style.side_effect = lambda text, **kwargs: f"STYLED({text})"

    output = """
ERROR: file1.py Imports are incorrectly sorted.
Skipped 1 files
"""

    formatted = format_tool_output(output.strip(), "isort")

    # Check that file paths are styled
    assert "STYLED(- " in formatted
    assert "import sorting required" in formatted
    assert "STYLED(Note: Skipped 1 files)" in formatted


@patch("click.style")
def test_format_tool_output_flake8(mock_style):
    """Test formatting flake8 output."""
    mock_style.side_effect = lambda text, **kwargs: f"STYLED({text})"

    output = """
file1.py:10:1: E302 expected 2 blank lines, found 1
file2.py:5:80: E501 line too long (100 > 88 characters)
"""

    formatted = format_tool_output(output.strip(), "flake8")

    # Check that file paths and error codes are styled
    assert "STYLED(- file1.py" in formatted
    assert "STYLED( : 10" in formatted
    assert "STYLED( : E302" in formatted
    assert "expected 2 blank lines, found 1" in formatted
    assert "STYLED(- file2.py" in formatted
    assert "STYLED( : 5" in formatted
    assert "STYLED( : E501" in formatted
    assert "line too long (100 > 88 characters)" in formatted


@pytest.mark.parametrize("tabulate_available", [True, False])
def test_format_as_table(tabulate_available):
    """Test formatting issues as a table."""
    from lintro.cli import format_as_table
    
    # Mock issues data
    issues = [
        {"path": "file1.py", "line": "10", "code": "E501", "message": "line too long"},
        {"path": "file2.py", "line": "20", "code": "E501", "message": "line too long"},
        {"path": "file3.py", "line": "30", "code": "E302", "message": "expected 2 blank lines"},
    ]
    
    # Mock tabulate availability
    with patch("lintro.cli.TABULATE_AVAILABLE", tabulate_available):
        if not tabulate_available:
            # Should return None if tabulate is not available
            assert format_as_table(issues, "flake8") is None
        else:
            # Mock tabulate function
            with patch("lintro.cli.tabulate", return_value="mocked table"):
                # Test file grouping
                result = format_as_table(issues, "flake8", "file")
                assert "Results for flake8" in result
                assert "mocked table" in result
                
                # Test code grouping
                result = format_as_table(issues, "flake8", "code")
                assert "Results for flake8" in result
                assert "mocked table" in result
                
                # Test no grouping
                result = format_as_table(issues, "flake8", "none")
                assert "Results for flake8" in result
                assert "mocked table" in result


def test_auto_grouping():
    """Test auto-grouping logic."""
    from lintro.cli import format_as_table
    
    # Mock issues data - more files than codes
    issues_more_files = [
        {"path": "file1.py", "line": "10", "code": "E501", "message": "line too long"},
        {"path": "file2.py", "line": "20", "code": "E501", "message": "line too long"},
        {"path": "file3.py", "line": "30", "code": "E501", "message": "line too long"},
        {"path": "file4.py", "line": "40", "code": "E501", "message": "line too long"},
        {"path": "file5.py", "line": "50", "code": "E302", "message": "expected 2 blank lines"},
    ]
    
    # Mock issues data - more codes than files
    issues_more_codes = [
        {"path": "file1.py", "line": "10", "code": "E501", "message": "line too long"},
        {"path": "file1.py", "line": "20", "code": "E302", "message": "expected 2 blank lines"},
        {"path": "file1.py", "line": "30", "code": "E303", "message": "too many blank lines"},
        {"path": "file1.py", "line": "40", "code": "E401", "message": "multiple imports"},
        {"path": "file2.py", "line": "50", "code": "F401", "message": "unused import"},
    ]
    
    # Mock tabulate function
    with patch("lintro.cli.TABULATE_AVAILABLE", True):
        with patch("lintro.cli.tabulate", return_value="mocked table"):
            # Test auto-grouping with more files than codes
            with patch("lintro.cli.format_as_table", wraps=format_as_table) as mock_format:
                result = format_as_table(issues_more_files, "flake8", "auto")
                # Should choose code grouping
                assert "PEP Code: E501" in result or "Code: E501" in result
                
            # Test auto-grouping with more codes than files
            with patch("lintro.cli.format_as_table", wraps=format_as_table) as mock_format:
                result = format_as_table(issues_more_codes, "flake8", "auto")
                # Should choose file grouping
                assert "File: file1.py" in result or "File: file2.py" in result


def test_tool_specific_formats():
    """Test tool-specific output formats."""
    from lintro.cli import format_as_table
    
    # Mock issues data for each tool
    black_issues = [
        {"path": "file1.py", "line": "N/A", "code": "FORMAT", "message": "formatting required"},
        {"path": "file2.py", "line": "N/A", "code": "FORMAT", "message": "formatting required"},
    ]
    
    isort_issues = [
        {"path": "file1.py", "line": "N/A", "code": "ISORT", "message": "import sorting required"},
        {"path": "file2.py", "line": "N/A", "code": "ISORT", "message": "import sorting required"},
    ]
    
    flake8_issues = [
        {"path": "file1.py", "line": "10", "code": "E501", "message": "line too long"},
        {"path": "file2.py", "line": "20", "code": "E302", "message": "expected 2 blank lines"},
    ]
    
    # Mock tabulate function
    with patch("lintro.cli.TABULATE_AVAILABLE", True):
        with patch("lintro.cli.tabulate", return_value="mocked table"):
            # Test Black format
            result = format_as_table(black_issues, "black", "none")
            assert "Results for black" in result
            
            # Test isort format
            result = format_as_table(isort_issues, "isort", "none")
            assert "Results for isort" in result
            
            # Test flake8 format
            result = format_as_table(flake8_issues, "flake8", "none")
            assert "Results for flake8" in result


def test_format_tool_output_with_table_format():
    """Test formatting tool output with table format."""
    from lintro.cli import format_tool_output
    
    # Mock Black output
    black_output = """
would reformat file1.py
would reformat file2.py

Oh no! 💥 💔 💥
2 files would be reformatted.
"""
    
    # Mock isort output
    isort_output = """
ERROR: file1.py Imports are incorrectly sorted and/or formatted.
ERROR: file2.py Imports are incorrectly sorted and/or formatted.
"""
    
    # Mock flake8 output
    flake8_output = """
file1.py:10:1: E501 line too long (100 > 88 characters)
file2.py:20:5: E302 expected 2 blank lines, found 1
"""
    
    # Mock tabulate and format_as_table
    with patch("lintro.cli.TABULATE_AVAILABLE", True):
        with patch("lintro.cli.format_as_table", return_value="mocked table output"):
            # Test with table format enabled
            result = format_tool_output(black_output, "black", True, "file")
            assert "mocked table output" in result
            
            result = format_tool_output(isort_output, "isort", True, "file")
            assert "mocked table output" in result
            
            result = format_tool_output(flake8_output, "flake8", True, "file")
            assert "mocked table output" in result
            
            # Test with different grouping options
            result = format_tool_output(flake8_output, "flake8", True, "code")
            assert "mocked table output" in result
            
            result = format_tool_output(flake8_output, "flake8", True, "none")
            assert "mocked table output" in result
            
            result = format_tool_output(flake8_output, "flake8", True, "auto")
            assert "mocked table output" in result 