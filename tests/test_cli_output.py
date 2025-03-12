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
def test_print_tool_header(mock_secho):
    """Test printing a tool header."""
    print_tool_header("test-tool", "check")
    assert mock_secho.call_count == 3
    # Check that the tool name and action are in the second call
    assert "test-tool" in mock_secho.call_args_list[1][0][0]
    assert "check" in mock_secho.call_args_list[1][0][0]


@patch("click.secho")
def test_print_tool_footer_success(mock_secho):
    """Test printing a tool footer for success."""
    print_tool_footer(True, 0)
    assert mock_secho.call_count == 2
    # Check that "No issues found" is in the first call
    assert "No issues found" in mock_secho.call_args_list[0][0][0]
    # Check that the color is green
    assert mock_secho.call_args_list[0][1]["fg"] == "green"


@patch("click.secho")
def test_print_tool_footer_failure(mock_secho):
    """Test printing a tool footer for failure."""
    print_tool_footer(False, 5)
    assert mock_secho.call_count == 2
    # Check that "Found 5 issues" is in the first call
    assert "Found 5 issues" in mock_secho.call_args_list[0][0][0]
    # Check that the color is red
    assert mock_secho.call_args_list[0][1]["fg"] == "red"


@patch("click.secho")
def test_print_summary(mock_secho):
    """Test printing a summary of tool results."""
    results = [
        ToolResult("tool1", True, "output1", 0),
        ToolResult("tool2", False, "output2", 3),
        ToolResult("tool3", False, "output3", 2),
    ]
    
    print_summary(results, "check")
    
    # Check that the summary header is printed
    assert any("Summary (check)" in call[0][0] for call in mock_secho.call_args_list)
    
    # Check that each tool is printed with its status
    assert any("tool1" in call[0][0] and "No issues" in call[0][0] for call in mock_secho.call_args_list)
    assert any("tool2" in call[0][0] and "3 issues" in call[0][0] for call in mock_secho.call_args_list)
    assert any("tool3" in call[0][0] and "2 issues" in call[0][0] for call in mock_secho.call_args_list)
    
    # Check that the total is printed
    assert any("Total: 5 issues found" in call[0][0] for call in mock_secho.call_args_list)


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
    
    # Check that "would reformat" lines are styled
    assert "STYLED(would reformat file1.py)" in formatted
    assert "STYLED(would reformat file2.py)" in formatted
    
    # Check that "Oh no!" line is styled
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
    
    # Check that "ERROR:" lines are styled
    assert "STYLED(ERROR: file1.py Imports are incorrectly sorted.)" in formatted
    
    # Check that "Skipped" line is styled
    assert "STYLED(Skipped 1 files)" in formatted


@patch("click.style")
def test_format_tool_output_flake8(mock_style):
    """Test formatting flake8 output."""
    mock_style.side_effect = lambda text, **kwargs: f"STYLED({text})"
    
    output = """
file1.py:10:1: E302 expected 2 blank lines, found 1
file2.py:5:80: E501 line too long (100 > 88 characters)
"""
    
    formatted = format_tool_output(output.strip(), "flake8")
    
    # Check that error lines are styled
    assert "STYLED(file1.py:10:1: E302 expected 2 blank lines, found 1)" in formatted
    assert "STYLED(file2.py:5:80: E501 line too long (100 > 88 characters))" in formatted 