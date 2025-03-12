"""Tests for improving coverage of Lintro CLI."""

import os
import re
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from lintro.cli import (
    ToolResult,
    count_issues,
    format_as_table,
    format_tool_output,
    get_relative_path,
    get_table_columns,
    parse_tool_list,
    print_summary,
    print_tool_footer,
    print_tool_header,
)


def test_print_summary_with_different_issue_counts():
    """Test print_summary with different issue counts."""
    # Test with no issues
    results = [
        ToolResult(name="black", success=True, output="All good", issues_count=0),
        ToolResult(name="flake8", success=True, output="All good", issues_count=0),
    ]
    
    file_obj = StringIO()
    print_summary(results, "Checking", file=file_obj)
    output = file_obj.getvalue()
    # The summary output contains the tool names and issue counts, not the actual output
    assert "black: ✓" in output
    assert "flake8: ✓" in output
    assert "Total issues: 0" in output
    
    # Test with a few issues (less than 10)
    results = [
        ToolResult(name="black", success=True, output="All good", issues_count=0),
        ToolResult(name="flake8", success=False, output="Issues found", issues_count=5),
    ]
    
    file_obj = StringIO()
    print_summary(results, "Checking", file=file_obj)
    output = file_obj.getvalue()
    assert "black: ✓" in output
    assert "flake8: ✗" in output
    assert "Total issues: 5" in output
    
    # Test with many issues (10 or more)
    results = [
        ToolResult(name="black", success=False, output="Issues found", issues_count=3),
        ToolResult(name="flake8", success=False, output="Issues found", issues_count=8),
    ]
    
    file_obj = StringIO()
    print_summary(results, "Checking", file=file_obj)
    output = file_obj.getvalue()
    assert "black: ✗" in output
    assert "flake8: ✗" in output
    assert "Total issues: 11" in output


def test_format_as_table_with_file_grouping():
    """Test format_as_table with file grouping and different issue types."""
    # Test with issues that have error and warning types
    issues = [
        {"file": "file1.py", "line": "10", "col": "5", "code": "E501", "message": "line too long", "type": "error"},
        {"file": "file1.py", "line": "20", "col": "10", "code": "W291", "message": "trailing whitespace", "type": "warning"},
        {"file": "file2.py", "line": "30", "col": "15", "code": "F401", "message": "unused import", "type": "error"},
    ]
    
    # Mock get_table_columns to return the expected values
    with patch("lintro.cli.get_table_columns", return_value=(["File", "Line", "Col", "Code", "Message"], ["file", "line", "col", "code", "message"])):
        with patch("lintro.cli.TABULATE_AVAILABLE", False):
            result = format_as_table(issues, "flake8", "file")
            
            # Verify that the result contains the issue information
            assert "file1.py" in result
            assert "file2.py" in result
            assert "E501" in result
            assert "W291" in result
            assert "F401" in result


def test_format_tool_output_with_pydocstyle():
    """Test format_tool_output with pydocstyle output."""
    # Test with pydocstyle output
    output = """
file1.py:10 in public function `foo`:
        D100: Missing docstring in public module
file2.py:20 in public class `Bar`:
        D101: Missing docstring in public class
"""
    
    # Test with table format
    with patch("lintro.cli.format_as_table", return_value="Formatted Table"):
        result = format_tool_output(output, "pydocstyle", use_table_format=True)
        assert result == "Formatted Table"
    
    # Test without table format
    result = format_tool_output(output, "pydocstyle", use_table_format=False)
    assert isinstance(result, str)
    assert "file1.py" in result or "D100" in result


def test_format_tool_output_with_darglint():
    """Test format_tool_output with darglint output."""
    # Test with darglint output
    output = """
file1.py:10: D101: Missing docstring in class (missing-docstring)
file2.py:20: D102: Missing docstring in method (missing-docstring)
"""
    
    # Test with table format
    with patch("lintro.cli.format_as_table", return_value="Formatted Table"):
        result = format_tool_output(output, "darglint", use_table_format=True)
        assert result == "Formatted Table"
    
    # Test without table format
    result = format_tool_output(output, "darglint", use_table_format=False)
    assert isinstance(result, str)
    assert "file1.py" in result or "D101" in result


def test_format_tool_output_with_darglint_timeout():
    """Test format_tool_output with darglint timeout output."""
    # Test with darglint output including timeout
    output = """
file1.py:10: D101: Missing docstring in class (missing-docstring)
Skipped file2.py (timeout after 10 seconds)
"""
    
    # Test with table format
    with patch("lintro.cli.format_as_table", return_value="Formatted Table"):
        result = format_tool_output(output, "darglint", use_table_format=True)
        assert result == "Formatted Table"
    
    # Test without table format
    result = format_tool_output(output, "darglint", use_table_format=False)
    assert isinstance(result, str)
    assert "file1.py" in result or "timeout" in result.lower()


def test_format_tool_output_with_hadolint():
    """Test format_tool_output with hadolint output."""
    # Test with hadolint output
    output = """
Dockerfile:10 DL3000 Use absolute WORKDIR
Dockerfile:20 DL3001 For some UNIX commands, COPY is more efficient than RUN
"""
    
    # Test with table format
    with patch("lintro.cli.format_as_table", return_value="Formatted Table"):
        result = format_tool_output(output, "hadolint", use_table_format=True)
        assert result == "Formatted Table"
    
    # Test without table format
    result = format_tool_output(output, "hadolint", use_table_format=False)
    assert isinstance(result, str)
    assert "Dockerfile" in result or "DL3000" in result


def test_format_tool_output_with_prettier():
    """Test format_tool_output with prettier output."""
    # Test with prettier output
    output = """
    file1.js 10:5 Delete `⏎`
    file2.js 20:10 Replace `'` with `"`
    """
    
    # Test with table format
    # First, let's check if the output is parsed correctly
    result = format_tool_output(output, "prettier", use_table_format=False)
    assert "file1.js" in result
    assert "Delete" in result
    
    # Now test with table format
    # We'll check if the function tries to parse the output
    parsed_output = format_tool_output(output, "prettier", use_table_format=True)
    assert isinstance(parsed_output, str)
    assert "file1.js" in parsed_output or "Delete" in parsed_output


def test_format_tool_output_with_eslint():
    """Test format_tool_output with eslint output."""
    # Test with eslint output
    output = """
    file1.js:10:5: 'x' is defined but never used. [Error/no-unused-vars]
    file2.js:20:10: Missing semicolon. [Error/semi]
    """
    
    # Test with table format
    # First, let's check if the output is parsed correctly
    result = format_tool_output(output, "eslint", use_table_format=False)
    assert "file1.js" in result
    assert "no-unused-vars" in result
    
    # Now test with table format
    # We'll check if the function tries to parse the output
    parsed_output = format_tool_output(output, "eslint", use_table_format=True)
    assert isinstance(parsed_output, str)
    assert "file1.js" in parsed_output or "no-unused-vars" in parsed_output


def test_format_tool_output_with_stylelint():
    """Test format_tool_output with stylelint output."""
    # Test with stylelint output
    output = """
    file1.css:10:5: Expected single space after ":" (declaration-colon-space-after)
    file2.css:20:10: Expected indentation of 2 spaces (indentation)
    """
    
    # Test with table format
    # First, let's check if the output is parsed correctly
    result = format_tool_output(output, "stylelint", use_table_format=False)
    assert "file1.css" in result
    assert "declaration-colon-space-after" in result
    
    # Now test with table format
    # We'll check if the function tries to parse the output
    parsed_output = format_tool_output(output, "stylelint", use_table_format=True)
    assert isinstance(parsed_output, str)
    assert "file1.css" in parsed_output or "declaration-colon-space-after" in parsed_output 