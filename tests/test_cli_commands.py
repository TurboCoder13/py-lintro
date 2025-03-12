"""Tests for Lintro CLI commands."""

import os
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from lintro.cli import cli, parse_tool_list


def test_parse_tool_list():
    """Test parsing a comma-separated list of tool names."""
    assert parse_tool_list(None) == []
    assert parse_tool_list("") == []
    assert parse_tool_list("black") == ["black"]
    assert parse_tool_list("black,isort") == ["black", "isort"]
    assert parse_tool_list("black, isort, flake8") == ["black", "isort", "flake8"]
    assert parse_tool_list(" black , isort , flake8 ") == ["black", "isort", "flake8"]


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_version(runner):
    """Test the --version option."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output


@patch("lintro.cli.AVAILABLE_TOOLS")
def test_list_tools_command(
    mock_tools,
    runner,
):
    """Test the list-tools command."""
    # Create mock tools
    mock_black = MagicMock()
    mock_black.name = "black"
    mock_black.description = "Black formatter"
    mock_black.can_fix = True

    mock_flake8 = MagicMock()
    mock_flake8.name = "flake8"
    mock_flake8.description = "Flake8 linter"
    mock_flake8.can_fix = False

    # Set up the mock to return our mock tools
    mock_tools.items.return_value = [
        ("black", mock_black),
        ("flake8", mock_flake8),
    ]

    # Run the command
    result = runner.invoke(cli, ["list-tools"])

    # Check the result
    assert result.exit_code == 0
    assert "black" in result.output
    assert "flake8" in result.output


@patch("lintro.cli.CHECK_TOOLS")
def test_check_command_with_table_format(
    mock_tools,
    runner,
):
    """Test the check command with table format."""
    # Mock the tools
    mock_tool = MagicMock()
    mock_tool.check.return_value = (True, "All good")
    mock_tools.items.return_value = [("black", mock_tool)]

    # Test with table format option
    with patch("lintro.cli.TABULATE_AVAILABLE", True):
        with patch("lintro.cli.format_tool_output") as mock_format:
            mock_format.return_value = "Formatted output"
            result = runner.invoke(cli, ["check", "--table-format", "."])
            assert result.exit_code == 0
            mock_format.assert_called_with("All good", "black", True, "auto")

    # Test with table format and group-by options
    with patch("lintro.cli.TABULATE_AVAILABLE", True):
        with patch("lintro.cli.format_tool_output") as mock_format:
            mock_format.return_value = "Formatted output"
            result = runner.invoke(
                cli, ["check", "--table-format", "--group-by", "file", "."]
            )
            assert result.exit_code == 0
            mock_format.assert_called_with("All good", "black", True, "file")

    # Test with table format and group-by code
    with patch("lintro.cli.TABULATE_AVAILABLE", True):
        with patch("lintro.cli.format_tool_output") as mock_format:
            mock_format.return_value = "Formatted output"
            result = runner.invoke(
                cli, ["check", "--table-format", "--group-by", "code", "."]
            )
            assert result.exit_code == 0
            mock_format.assert_called_with("All good", "black", True, "code")

    # Test with table format and group-by none
    with patch("lintro.cli.TABULATE_AVAILABLE", True):
        with patch("lintro.cli.format_tool_output") as mock_format:
            mock_format.return_value = "Formatted output"
            result = runner.invoke(
                cli, ["check", "--table-format", "--group-by", "none", "."]
            )
            assert result.exit_code == 0
            mock_format.assert_called_with("All good", "black", True, "none")


@patch("lintro.cli.FIX_TOOLS")
def test_fmt_command_with_table_format(
    mock_tools,
    runner,
):
    """Test the fmt command with table format."""
    # Mock the tools
    mock_tool = MagicMock()
    mock_tool.fix.return_value = (True, "All fixed")
    mock_tools.items.return_value = [("black", mock_tool)]

    # Test with table format option
    with patch("lintro.cli.TABULATE_AVAILABLE", True):
        with patch("lintro.cli.format_tool_output") as mock_format:
            mock_format.return_value = "Formatted output"
            result = runner.invoke(cli, ["fmt", "--table-format", "."])
            assert result.exit_code == 0
            mock_format.assert_called_with("All fixed", "black", True, "auto")

    # Test with table format and group-by options
    with patch("lintro.cli.TABULATE_AVAILABLE", True):
        with patch("lintro.cli.format_tool_output") as mock_format:
            mock_format.return_value = "Formatted output"
            result = runner.invoke(
                cli, ["fmt", "--table-format", "--group-by", "file", "."]
            )
            assert result.exit_code == 0
            mock_format.assert_called_with("All fixed", "black", True, "file")

    # Test with table format and group-by code
    with patch("lintro.cli.TABULATE_AVAILABLE", True):
        with patch("lintro.cli.format_tool_output") as mock_format:
            mock_format.return_value = "Formatted output"
            result = runner.invoke(
                cli, ["fmt", "--table-format", "--group-by", "code", "."]
            )
            assert result.exit_code == 0
            mock_format.assert_called_with("All fixed", "black", True, "code")

    # Test with table format and group-by none
    with patch("lintro.cli.TABULATE_AVAILABLE", True):
        with patch("lintro.cli.format_tool_output") as mock_format:
            mock_format.return_value = "Formatted output"
            result = runner.invoke(
                cli, ["fmt", "--table-format", "--group-by", "none", "."]
            )
            assert result.exit_code == 0
            mock_format.assert_called_with("All fixed", "black", True, "none")


@patch("lintro.cli.TABULATE_AVAILABLE", False)
def test_table_format_fallback(runner):
    """Test fallback when tabulate is not available."""
    with patch("click.echo") as mock_echo:
        result = runner.invoke(cli, ["check", "--table-format", "."])
        # Should show a warning
        mock_echo.assert_any_call(
            "Warning: Table formatting requested but tabulate package is not installed.",
            err=True,
        )


def test_tools_executed_in_alphabetical_order():
    """Test that tools are executed in alphabetical order."""
    from unittest.mock import patch, MagicMock
    from click.testing import CliRunner
    from lintro.cli import cli
    
    # Create mock tools with different names
    mock_tools = {
        "ztool": MagicMock(),
        "atool": MagicMock(),
        "mtool": MagicMock(),
    }
    
    # Track the order of execution
    execution_order = []
    
    # Create a side effect function to record the order
    def record_execution(name, *args, **kwargs):
        execution_order.append(name)
        return True, "No issues found."
    
    # Set up the check method for each mock tool
    for name, tool in mock_tools.items():
        tool.check.side_effect = lambda paths, name=name: record_execution(name, paths)
    
    # Patch the CHECK_TOOLS dictionary
    with patch("lintro.cli.CHECK_TOOLS", mock_tools):
        runner = CliRunner()
        result = runner.invoke(cli, ["check", "--tools", "ztool,atool,mtool", "."])
        
        # Verify the execution order is alphabetical
        assert execution_order == ["atool", "mtool", "ztool"]


def test_mypy_output_formatting():
    """Test that mypy output is properly formatted in a table."""
    from lintro.cli import format_tool_output
    
    # Sample mypy output
    mypy_output = """
file1.py:10: error: Missing return type annotation for function "test_func"  [no-untyped-def]
file1.py:15: note: Use "-> None" if function does not return a value
file2.py:20: error: "list" is not subscriptable, use "typing.List" instead  [misc]
"""
    
    # Test with table format
    with patch("lintro.cli.TABULATE_AVAILABLE", True):
        with patch("lintro.cli.format_as_table") as mock_format_table:
            mock_format_table.return_value = "Formatted table"
            result = format_tool_output(mypy_output, "mypy", True, "file")
            
            # Verify format_as_table was called with the correct issues
            args, _ = mock_format_table.call_args
            issues = args[0]
            
            # Check that we have 3 issues
            assert len(issues) == 3
            
            # Check the first issue
            assert issues[0]["file"] == "file1.py"
            assert issues[0]["line"] == "10"
            assert issues[0]["code"] == "no-untyped-def"
            assert "Missing return type" in issues[0]["message"]
            
            # Check the second issue
            assert issues[1]["file"] == "file1.py"
            assert issues[1]["line"] == "15"
            assert issues[1]["code"] == "NOTE"
            assert "Use \"-> None\"" in issues[1]["message"]
            
            # Check the third issue
            assert issues[2]["file"] == "file2.py"
            assert issues[2]["line"] == "20"
            assert issues[2]["code"] == "misc"
            assert "\"list\" is not subscriptable" in issues[2]["message"]


def test_pylint_column_ordering():
    """Test that pylint output has the Name column before the Message column."""
    from lintro.cli import get_table_columns
    
    # Create sample pylint issues
    issues = [
        {
            "file": "test.py",
            "code": "W0612",
            "line": "10",
            "col": "4",
            "name": "unused-variable",
            "message": "Unused variable 'foo'"
        }
    ]
    
    # Get the columns for pylint with file grouping
    display_columns, _ = get_table_columns(issues, "pylint", "file")
    
    # Check that the Name column comes before the Message column
    name_index = display_columns.index("Name")
    message_index = display_columns.index("Message")
    assert name_index < message_index, "Name column should come before Message column for pylint output"
    
    # When grouped by file, the File column is removed
    expected_order = ["Pylint Code", "Line", "Position", "Name", "Message"]
    assert display_columns == expected_order, f"Expected column order {expected_order}, got {display_columns}"
    
    # Also test with no grouping to ensure all columns are present
    display_columns_no_group, _ = get_table_columns(issues, "pylint", "none")
    
    # Check that the Name column comes before the Message column
    name_index = display_columns_no_group.index("Name")
    message_index = display_columns_no_group.index("Message")
    assert name_index < message_index, "Name column should come before Message column for pylint output"
    
    # With no grouping, all columns should be present
    expected_order_no_group = ["File", "Pylint Code", "Line", "Position", "Name", "Message"]
    assert display_columns_no_group == expected_order_no_group, f"Expected column order {expected_order_no_group}, got {display_columns_no_group}"


def test_separate_tables_for_groups():
    """Test that format_as_table creates a single table with group headers when grouping by file or code."""
    from lintro.cli import format_as_table
    
    # Create sample issues with multiple files and codes
    issues = [
        {
            "file": "file1.py",
            "code": "E101",
            "line": "10",
            "message": "Error 1"
        },
        {
            "file": "file1.py",
            "code": "W201",
            "line": "20",
            "message": "Warning 1"
        },
        {
            "file": "file2.py",
            "code": "E101",
            "line": "30",
            "message": "Error 2"
        }
    ]
    
    # Test with file grouping
    with patch("lintro.cli.tabulate") as mock_tabulate:
        # Set up the mock to return a simple table with separator lines
        mock_tabulate.return_value = "+-----+-----+\n| Col1 | Col2 |\n+-----+-----+\n| A   | B   |\n+-----+-----+"
        
        # Format with file grouping
        result = format_as_table(issues, "flake8", "file")
        
        # Verify that tabulate was called once with all rows
        assert mock_tabulate.call_count == 1, f"Expected tabulate to be called once for file grouping, got {mock_tabulate.call_count}"
        
        # For file grouping, we now post-process the table to add file headers
        # So we need to check the final result string instead of the rows passed to tabulate
        assert "File: file1.py" in result, "Expected file1.py header in the result"
        assert "File: file2.py" in result, "Expected file2.py header in the result"
        
        # Verify that the result contains parts of the mocked table
        assert "Col1" in result, "Expected column header in the result"
        assert "Col2" in result, "Expected column header in the result"
    
    # Test with code grouping
    with patch("lintro.cli.tabulate") as mock_tabulate:
        # Set up the mock to return a simple table with separator lines
        mock_tabulate.return_value = "+-----+-----+\n| Col1 | Col2 |\n+-----+-----+\n| A   | B   |\n+-----+-----+"
        
        # Format with code grouping
        result = format_as_table(issues, "flake8", "code")
        
        # Verify that tabulate was called once with all rows
        assert mock_tabulate.call_count == 1, f"Expected tabulate to be called once for code grouping, got {mock_tabulate.call_count}"
        
        # For code grouping, we now post-process the table to add code headers
        # So we need to check the final result string instead of the rows passed to tabulate
        assert "PEP Code: E101" in result, "Expected E101 code header in the result"
        assert "PEP Code: W201" in result, "Expected W201 code header in the result"
        
        # Verify that the result contains parts of the mocked table
        assert "Col1" in result, "Expected column header in the result"
        assert "Col2" in result, "Expected column header in the result"
