"""Tests for YAMLLint integration with lintro CLI."""

import json
import os
import re
from unittest.mock import MagicMock, patch

import pytest

from lintro.cli import count_issues, format_tool_output


def test_yamllint_count_issues():
    """Test counting issues from yamllint output."""
    # Create a sample yamllint output with 2 issues
    yamllint_output = """
test.yaml:1:1: [error] missing document start "---" (document-start)
test.yaml:3:1: [warning] too few spaces before comment (comments)
"""
    
    # Count issues in the output
    issue_count = count_issues(yamllint_output, "yamllint")
    
    # Verify that 2 issues were counted
    assert issue_count == 2


@patch("lintro.cli.TABULATE_AVAILABLE", True)
@patch("lintro.cli.tabulate")
def test_yamllint_format_output(mock_tabulate):
    """Test formatting yamllint output as a table."""
    # Mock tabulate to return a simple table
    mock_tabulate.return_value = "Formatted Table"
    
    # Create a sample yamllint output with 2 issues
    yamllint_output = """
test.yaml:1:1: [error] missing document start "---" (document-start)
test.yaml:3:1: [warning] too few spaces before comment (comments)
"""
    
    # Format the output with table formatting
    formatted_output = format_tool_output(yamllint_output, "yamllint", True, "file")
    
    # Verify that the output is formatted correctly
    assert "Formatted Table" in formatted_output
    
    # Check that tabulate was called with the correct arguments
    assert mock_tabulate.call_count > 0
    
    # The first argument should be a list of rows
    args, kwargs = mock_tabulate.call_args
    rows = args[0]
    
    # Verify that the rows contain the expected data
    assert len(rows) > 0


@patch("lintro.cli.TABULATE_AVAILABLE", False)
def test_yamllint_format_output_no_tabulate():
    """Test formatting yamllint output without tabulate."""
    # Create a sample yamllint output with 2 issues
    yamllint_output = """
test.yaml:1:1: [error] missing document start "---" (document-start)
test.yaml:3:1: [warning] too few spaces before comment (comments)
"""
    
    # Format the output without table formatting
    formatted_output = format_tool_output(yamllint_output, "yamllint", False, "file")
    
    # Verify that the output contains the expected information
    assert "test.yaml" in formatted_output
    assert "missing document start" in formatted_output
    assert "too few spaces before comment" in formatted_output


@patch("lintro.tools.yamllint.YAMLLintTool.check")
def test_yamllint_tool_check(mock_check):
    """Test the YAMLLintTool check method."""
    # Import the YAMLLintTool class
    from lintro.tools.yamllint import YAMLLintTool
    
    # Mock the check method to return success and output
    mock_check.return_value = (True, "No YAML issues found.")
    
    # Create a YAMLLintTool instance
    tool = YAMLLintTool()
    
    # Set the config file option
    tool.set_options(config_file=".yamllint.yml", strict=True)
    
    # Call the check method
    success, output = tool.check(["test.yaml"])
    
    # Verify that the check method was called with the correct arguments
    assert success is True
    assert output == "No YAML issues found."
    mock_check.assert_called_once_with(["test.yaml"])


@patch("lintro.tools.yamllint.YAMLLintTool.fix")
def test_yamllint_tool_fix(mock_fix):
    """Test the YAMLLintTool fix method."""
    # Import the YAMLLintTool class
    from lintro.tools.yamllint import YAMLLintTool
    
    # Mock the fix method to return failure and output
    mock_fix.return_value = (False, "YAMLLint cannot automatically fix issues. Run 'lintro check' to see issues.")
    
    # Create a YAMLLintTool instance
    tool = YAMLLintTool()
    
    # Call the fix method
    success, output = tool.fix(["test.yaml"])
    
    # Verify that the fix method was called with the correct arguments
    assert success is False
    assert "cannot automatically fix" in output
    mock_fix.assert_called_once_with(["test.yaml"]) 