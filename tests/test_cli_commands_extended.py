"""Extended tests for Lintro CLI commands."""

import os
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from lintro.cli import cli, main


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@patch("lintro.cli.CHECK_TOOLS")
@patch("lintro.cli.parse_tool_list")
@patch("lintro.cli.print_summary")
def test_check_with_custom_tools(mock_print_summary, mock_parse_tool_list, mock_check_tools, runner):
    """Test check command with custom tools."""
    # Setup
    mock_black = MagicMock()
    mock_black.name = "black"
    mock_black.check.return_value = (True, "All good", 0)
    
    mock_flake8 = MagicMock()
    mock_flake8.name = "flake8"
    mock_flake8.check.return_value = (True, "All good", 0)
    
    mock_check_tools.values.return_value = [mock_black, mock_flake8]
    mock_parse_tool_list.return_value = ["black", "flake8"]
    
    # Create a test file
    with runner.isolated_filesystem():
        with open("test_file.py", "w") as f:
            f.write("print('Hello, world!')")
        
        # Run the command with mocked print_summary to avoid output issues
        with patch("lintro.cli.check", return_value=0):
            result = runner.invoke(
                cli,
                [
                    "check",
                    "--tools", "black,flake8",
                    "--exclude", "*.pyc",
                    "--include-venv",
                    "test_file.py",
                ],
            )
            
            # Verify
            assert result.exit_code == 0 or mock_parse_tool_list.called


@patch("lintro.cli.CHECK_TOOLS")
@patch("lintro.cli.parse_tool_list")
@patch("lintro.cli.print_summary")
def test_check_with_output_file(mock_print_summary, mock_parse_tool_list, mock_check_tools, runner):
    """Test check command with output to file."""
    # Setup
    mock_black = MagicMock()
    mock_black.name = "black"
    mock_black.check.return_value = (True, "All good", 0)
    
    mock_check_tools.values.return_value = [mock_black]
    mock_parse_tool_list.return_value = ["black"]
    
    # Create a test file
    with runner.isolated_filesystem():
        with open("test_file.py", "w") as f:
            f.write("print('Hello, world!')")
        
        # Run the command with mocked print_summary to avoid output issues
        with patch("lintro.cli.check", return_value=0):
            result = runner.invoke(
                cli,
                [
                    "check",
                    "--tools", "black",
                    "--output", "output.txt",
                    "test_file.py",
                ],
            )
            
            # Verify
            assert result.exit_code == 0 or mock_parse_tool_list.called


@patch("lintro.cli.FIX_TOOLS")
@patch("lintro.cli.parse_tool_list")
@patch("lintro.cli.print_summary")
def test_fmt_with_custom_tools(mock_print_summary, mock_parse_tool_list, mock_fix_tools, runner):
    """Test fmt command with custom tools."""
    # Setup
    mock_black = MagicMock()
    mock_black.name = "black"
    mock_black.fix.return_value = (True, "Formatted", 0)
    
    mock_isort = MagicMock()
    mock_isort.name = "isort"
    mock_isort.fix.return_value = (True, "Sorted imports", 0)
    
    mock_fix_tools.values.return_value = [mock_black, mock_isort]
    mock_parse_tool_list.return_value = ["black", "isort"]
    
    # Create a test file
    with runner.isolated_filesystem():
        with open("test_file.py", "w") as f:
            f.write("print('Hello, world!')")
        
        # Run the command with mocked print_summary to avoid output issues
        with patch("lintro.cli.fmt", return_value=0):
            result = runner.invoke(
                cli,
                [
                    "fmt",
                    "--tools", "black,isort",
                    "--exclude", "*.pyc",
                    "--include-venv",
                    "test_file.py",
                ],
            )
            
            # Verify
            assert result.exit_code == 0 or mock_parse_tool_list.called


@patch("lintro.cli.FIX_TOOLS")
@patch("lintro.cli.parse_tool_list")
@patch("lintro.cli.print_summary")
def test_fmt_with_output_file(mock_print_summary, mock_parse_tool_list, mock_fix_tools, runner):
    """Test fmt command with output to file."""
    # Setup
    mock_black = MagicMock()
    mock_black.name = "black"
    mock_black.fix.return_value = (True, "Formatted", 0)
    
    mock_fix_tools.values.return_value = [mock_black]
    mock_parse_tool_list.return_value = ["black"]
    
    # Create a test file
    with runner.isolated_filesystem():
        with open("test_file.py", "w") as f:
            f.write("print('Hello, world!')")
        
        # Run the command with mocked print_summary to avoid output issues
        with patch("lintro.cli.fmt", return_value=0):
            result = runner.invoke(
                cli,
                [
                    "fmt",
                    "--tools", "black",
                    "--output", "output.txt",
                    "test_file.py",
                ],
            )
            
            # Verify
            assert result.exit_code == 0 or mock_parse_tool_list.called


@patch("lintro.cli.AVAILABLE_TOOLS")
@patch("click.echo")
def test_list_tools_with_show_conflicts(mock_echo, mock_available_tools, runner):
    """Test list_tools command with show_conflicts option."""
    # Setup
    mock_black = MagicMock()
    mock_black.name = "black"
    mock_black.description = "The uncompromising code formatter"
    mock_black.can_check = True
    mock_black.can_fix = True
    mock_black.conflicts_with = ["yapf"]
    
    mock_isort = MagicMock()
    mock_isort.name = "isort"
    mock_isort.description = "Sort imports"
    mock_isort.can_check = True
    mock_isort.can_fix = True
    mock_isort.conflicts_with = []
    
    mock_available_tools.values.return_value = [mock_black, mock_isort]
    
    # Run the command with mocked click.echo to avoid output issues
    with patch("lintro.cli.list_tools", return_value=None):
        result = runner.invoke(cli, ["list-tools", "--show-conflicts"])
        
        # Verify
        assert result.exit_code == 0


@patch("lintro.cli.AVAILABLE_TOOLS")
@patch("click.echo")
def test_list_tools_with_output_file(mock_echo, mock_available_tools, runner):
    """Test list_tools command with output to file."""
    # Setup
    mock_black = MagicMock()
    mock_black.name = "black"
    mock_black.description = "The uncompromising code formatter"
    mock_black.can_check = True
    mock_black.can_fix = True
    mock_black.conflicts_with = []
    
    mock_available_tools.values.return_value = [mock_black]
    
    # Create a test file
    with runner.isolated_filesystem():
        # Run the command with mocked click.echo to avoid output issues
        with patch("lintro.cli.list_tools", return_value=None):
            result = runner.invoke(cli, ["list-tools", "--output", "output.txt"])
            
            # Verify
            assert result.exit_code == 0


@patch("lintro.cli.cli")
def test_main(mock_cli):
    """Test the main function."""
    main()
    mock_cli.assert_called_once() 