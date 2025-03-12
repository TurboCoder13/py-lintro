"""Tests for Lintro CLI output formatting."""

from unittest.mock import MagicMock, patch

import pytest

from lintro.cli import (
    ToolResult,
    count_issues,
    format_tool_output,
    print_summary,
    print_tool_footer,
    print_tool_header,
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
@patch("click.echo")
def test_print_tool_header(mock_echo, mock_secho):
    """Test printing a tool header."""
    print_tool_header("test-tool", "check")
    assert mock_echo.call_count > 0
    assert any("test-tool" in call[0][0] for call in mock_echo.call_args_list)
    assert any("check" in call[0][0] for call in mock_echo.call_args_list)


@patch("click.secho")
@patch("click.echo")
def test_print_tool_footer_success(mock_echo, mock_secho):
    """Test printing a tool footer for success."""
    print_tool_footer(True, 0, tool_name="test-tool")
    assert mock_echo.call_count > 0
    assert any("No issues found" in call[0][0] for call in mock_echo.call_args_list)


@patch("click.secho")
@patch("click.echo")
def test_print_tool_footer_failure(mock_echo, mock_secho):
    """Test printing a tool footer for failure."""
    print_tool_footer(False, 5, tool_name="test-tool")
    assert mock_echo.call_count > 0
    assert any("Found 5 issues" in call[0][0] for call in mock_echo.call_args_list)


@patch("click.secho")
@patch("click.echo")
@patch("lintro.cli.read_ascii_art")
def test_print_summary_with_ascii_art(
    mock_read_ascii_art,
    mock_echo,
    mock_secho,
):
    """Test that print_summary includes ASCII art based on results."""
    # Mock the read_ascii_art function to return a simple ASCII art
    mock_read_ascii_art.return_value = ["ASCII art"]
    
    # Test with all successful results
    successful_results = [
        ToolResult(name="tool1", success=True, output="output1", issues_count=0),
        ToolResult(name="tool2", success=True, output="output2", issues_count=0),
    ]
    
    print_summary(successful_results, "check")
    
    # Verify that read_ascii_art was called with "success.txt"
    mock_read_ascii_art.assert_called_with("success.txt")
    
    # Reset the mock
    mock_read_ascii_art.reset_mock()
    
    # Test with some failed results
    failed_results = [
        ToolResult(name="tool1", success=True, output="output1", issues_count=0),
        ToolResult(name="tool2", success=False, output="output2", issues_count=3),
    ]
    
    print_summary(failed_results, "check")
    
    # Verify that read_ascii_art was called with "fail.txt"
    mock_read_ascii_art.assert_called_with("fail.txt")
    
    # Verify that the ASCII art is included in the output
    assert any("ASCII art" in call[0][0] for call in mock_echo.call_args_list)


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

    # In our new implementation, we just pass through the original output
    assert "would reformat file1.py" in formatted
    assert "would reformat file2.py" in formatted
    assert "Oh no! 💥 💔 💥" in formatted
    assert "2 files would be reformatted" in formatted


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
        {
            "path": "file3.py",
            "line": "30",
            "code": "E302",
            "message": "expected 2 blank lines",
        },
    ]

    # Mock tabulate availability
    with patch("lintro.cli.TABULATE_AVAILABLE", tabulate_available):
        if not tabulate_available:
            # In our new implementation, we always return a table
            result = format_as_table(issues, "flake8")
            assert result is not None
            assert "PEP Code" in result
        else:
            # Mock tabulate function
            with patch("lintro.cli.tabulate", return_value="mocked table"):
                # Test file grouping
                result = format_as_table(issues, "flake8", "file")
                assert "mocked table" in result

                # Test code grouping
                result = format_as_table(issues, "flake8", "code")
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
        {
            "path": "file5.py",
            "line": "50",
            "code": "E302",
            "message": "expected 2 blank lines",
        },
    ]

    # Mock issues data - more codes than files
    issues_more_codes = [
        {"path": "file1.py", "line": "10", "code": "E501", "message": "line too long"},
        {
            "path": "file1.py",
            "line": "20",
            "code": "E302",
            "message": "expected 2 blank lines",
        },
        {
            "path": "file1.py",
            "line": "30",
            "code": "E303",
            "message": "too many blank lines",
        },
        {
            "path": "file1.py",
            "line": "40",
            "code": "E401",
            "message": "multiple imports",
        },
        {"path": "file2.py", "line": "50", "code": "F401", "message": "unused import"},
    ]

    # Mock tabulate function
    with patch("lintro.cli.TABULATE_AVAILABLE", True):
        with patch("lintro.cli.tabulate", return_value="mocked table"):
            # Test auto-grouping with more files than codes
            result = format_as_table(issues_more_files, "flake8", "auto")
            # Just verify we get a table back
            assert "mocked table" in result

            # Test auto-grouping with more codes than files
            result = format_as_table(issues_more_codes, "flake8", "auto")
            # Just verify we get a table back
            assert "mocked table" in result


def test_tool_specific_formats():
    """Test tool-specific output formats."""
    from lintro.cli import format_as_table

    # Mock issues data for each tool
    black_issues = [
        {
            "path": "file1.py",
            "line": "N/A",
            "code": "FORMAT",
            "message": "formatting required",
        },
        {
            "path": "file2.py",
            "line": "N/A",
            "code": "FORMAT",
            "message": "formatting required",
        },
    ]

    isort_issues = [
        {
            "path": "file1.py",
            "line": "N/A",
            "code": "ISORT",
            "message": "import sorting required",
        },
        {
            "path": "file2.py",
            "line": "N/A",
            "code": "ISORT",
            "message": "import sorting required",
        },
    ]

    flake8_issues = [
        {"path": "file1.py", "line": "10", "code": "E501", "message": "line too long"},
        {
            "path": "file2.py",
            "line": "20",
            "code": "E302",
            "message": "expected 2 blank lines",
        },
    ]

    # Mock tabulate function
    with patch("lintro.cli.TABULATE_AVAILABLE", True):
        with patch("lintro.cli.tabulate", return_value="mocked table"):
            # Test Black format
            result = format_as_table(black_issues, "black", "none")
            assert "mocked table" in result

            # Test isort format
            result = format_as_table(isort_issues, "isort", "none")
            assert "mocked table" in result

            # Test flake8 format
            result = format_as_table(flake8_issues, "flake8", "none")
            assert "mocked table" in result


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
    assert mock_echo.call_count > 0
    assert any("Summary of check" in call[0][0] for call in mock_echo.call_args_list)

    # Check that each tool is mentioned in the output
    assert any("tool1" in call[0][0] for call in mock_echo.call_args_list)
    assert any("tool2" in call[0][0] for call in mock_echo.call_args_list)
    assert any("tool3" in call[0][0] for call in mock_echo.call_args_list)

    # Check total issues
    assert any("Total issues: 5" in call[0][0] for call in mock_echo.call_args_list)
