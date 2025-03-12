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
            mock_format.assert_called_with("All good", "black", True, "file")

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
