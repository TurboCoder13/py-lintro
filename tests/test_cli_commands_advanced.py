"""Tests for CLI commands."""

import os
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

import click
import pytest
from click.testing import CliRunner

from lintro.cli import cli, check, fmt, list_tools
from lintro.tools import CHECK_TOOLS, FIX_TOOLS


def test_main_with_invalid_command():
    """Test main function with invalid command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["invalid-command"])
    
    assert result.exit_code == 2
    assert "No such command" in result.output


def test_main_with_help_flag():
    """Test main function with help flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_check_with_no_tools():
    """Test check command with no tools specified."""
    # Mock the CHECK_TOOLS dictionary to be empty
    with patch("lintro.cli.CHECK_TOOLS", {}):
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a dummy file
            with open("test_file.py", "w") as f:
                f.write("print('hello')")
            
            result = runner.invoke(cli, ["check", "test_file.py"])
            
            assert result.exit_code == 1
            assert "No tools selected" in result.output


def test_check_with_no_files():
    """Test check command with no files specified."""
    # Mock os.getcwd to return a known path
    with patch("os.getcwd", return_value="/test/path"):
        # Mock a tool that will be called
        mock_tool = MagicMock()
        mock_tool.check.return_value = (True, "No issues found")
        mock_tool.set_options = MagicMock()
        
        with patch("lintro.cli.CHECK_TOOLS", {"black": mock_tool}):
            # We need to patch sys.exit to prevent the command from exiting
            with patch("sys.exit"):
                runner = CliRunner()
                result = runner.invoke(cli, ["check", "--tools", "black"])
                
                # The output should contain "Running black"
                assert "Running black" in result.output
                # The mock tool should have been called
                assert mock_tool.check.called


def test_check_with_tools_and_files():
    """Test check command with tools and files specified."""
    # Create mock tools
    mock_black = MagicMock()
    mock_black.check.return_value = (True, "No issues found")
    mock_black.set_options = MagicMock()
    
    mock_flake8 = MagicMock()
    mock_flake8.check.return_value = (False, "Issues found")
    mock_flake8.set_options = MagicMock()
    
    # Patch the CHECK_TOOLS dictionary and sys.exit to prevent the command from exiting
    with patch("lintro.cli.CHECK_TOOLS", {"black": mock_black, "flake8": mock_flake8}):
        with patch("sys.exit"):
            runner = CliRunner()
            with runner.isolated_filesystem():
                # Create dummy files
                with open("file1.py", "w") as f:
                    f.write("print('hello')")
                with open("file2.py", "w") as f:
                    f.write("print('world')")
                
                result = runner.invoke(cli, ["check", "--tools", "black,flake8", "file1.py", "file2.py"])
                
                # The output should contain both tool names
                assert "Running black" in result.output
                assert "Running flake8" in result.output
                
                # Check that both tools were called
                assert mock_black.check.called
                assert mock_flake8.check.called


def test_fmt_with_tools_and_files():
    """Test fmt command with tools and files specified."""
    # Create a mock for the fmt command
    mock_fmt_cmd = MagicMock()
    
    # Find the fmt command in the CLI group
    fmt_cmd = None
    for cmd_name, cmd in cli.commands.items():
        if cmd_name == "fmt":
            fmt_cmd = cmd
            break
    
    # Save the original callback
    original_callback = fmt_cmd.callback
    
    try:
        # Replace the callback with our mock
        fmt_cmd.callback = mock_fmt_cmd
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create dummy files
            with open("file1.py", "w") as f:
                f.write("print('hello')")
            with open("file2.py", "w") as f:
                f.write("print('world')")
            
            result = runner.invoke(cli, ["fmt", "--tools", "black,isort", "file1.py", "file2.py"])
            
            # The mock should have been called
            assert mock_fmt_cmd.called
            # Check that the tools option was passed
            args, kwargs = mock_fmt_cmd.call_args
            assert kwargs["tools"] == "black,isort"
            # Check that the paths were passed
            assert "file1.py" in kwargs["paths"]
            assert "file2.py" in kwargs["paths"]
    finally:
        # Restore the original callback
        fmt_cmd.callback = original_callback


def test_list_tools_command():
    """Test list_tools command."""
    # Create mock tools
    mock_black = MagicMock()
    mock_black.description = "Black code formatter"
    mock_black.can_fix = True
    mock_black.config = MagicMock()
    mock_black.config.conflicts_with = []
    mock_black.config.priority = 100
    
    mock_flake8 = MagicMock()
    mock_flake8.description = "Flake8 linter"
    mock_flake8.can_fix = False
    mock_flake8.config = MagicMock()
    mock_flake8.config.conflicts_with = []
    mock_flake8.config.priority = 200
    
    # Patch the AVAILABLE_TOOLS dictionary
    with patch("lintro.cli.AVAILABLE_TOOLS", {"black": mock_black, "flake8": mock_flake8}):
        runner = CliRunner()
        result = runner.invoke(cli, ["list-tools"])
        
        assert result.exit_code == 0
        assert "Available tools:" in result.output
        assert "black" in result.output
        assert "flake8" in result.output


# For the remaining tests, we'll use a different approach
# We'll patch the actual command functions in the Click commands

def test_cli_check_command():
    """Test CLI check command."""
    # Create a mock for the check command
    mock_check_cmd = MagicMock()
    
    # Find the check command in the CLI group
    check_cmd = None
    for cmd_name, cmd in cli.commands.items():
        if cmd_name == "check":
            check_cmd = cmd
            break
    
    # Save the original callback
    original_callback = check_cmd.callback
    
    try:
        # Replace the callback with our mock
        check_cmd.callback = mock_check_cmd
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a dummy file
            with open("file1.py", "w") as f:
                f.write("print('hello')")
            
            result = runner.invoke(cli, ["check", "--tools", "black", "file1.py"])
            
            # The mock should have been called
            assert mock_check_cmd.called
    finally:
        # Restore the original callback
        check_cmd.callback = original_callback


def test_cli_fmt_command():
    """Test CLI fmt command."""
    # Create a mock for the fmt command
    mock_fmt_cmd = MagicMock()
    
    # Find the fmt command in the CLI group
    fmt_cmd = None
    for cmd_name, cmd in cli.commands.items():
        if cmd_name == "fmt":
            fmt_cmd = cmd
            break
    
    # Save the original callback
    original_callback = fmt_cmd.callback
    
    try:
        # Replace the callback with our mock
        fmt_cmd.callback = mock_fmt_cmd
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a dummy file
            with open("file1.py", "w") as f:
                f.write("print('hello')")
            
            result = runner.invoke(cli, ["fmt", "--tools", "black", "file1.py"])
            
            # The mock should have been called
            assert mock_fmt_cmd.called
    finally:
        # Restore the original callback
        fmt_cmd.callback = original_callback


def test_cli_list_tools_command():
    """Test CLI list-tools command."""
    # Create a mock for the list-tools command
    mock_list_tools_cmd = MagicMock()
    
    # Find the list-tools command in the CLI group
    list_tools_cmd = None
    for cmd_name, cmd in cli.commands.items():
        if cmd_name == "list-tools":
            list_tools_cmd = cmd
            break
    
    # Save the original callback
    original_callback = list_tools_cmd.callback
    
    try:
        # Replace the callback with our mock
        list_tools_cmd.callback = mock_list_tools_cmd
        
        runner = CliRunner()
        result = runner.invoke(cli, ["list-tools"])
        
        # The mock should have been called
        assert mock_list_tools_cmd.called
    finally:
        # Restore the original callback
        list_tools_cmd.callback = original_callback


def test_cli_with_group_by_option():
    """Test CLI with group-by option."""
    # Create a mock for the check command
    mock_check_cmd = MagicMock()
    
    # Find the check command in the CLI group
    check_cmd = None
    for cmd_name, cmd in cli.commands.items():
        if cmd_name == "check":
            check_cmd = cmd
            break
    
    # Save the original callback
    original_callback = check_cmd.callback
    
    try:
        # Replace the callback with our mock
        check_cmd.callback = mock_check_cmd
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a dummy file
            with open("file1.py", "w") as f:
                f.write("print('hello')")
            
            result = runner.invoke(cli, ["check", "--tools", "black", "--group-by", "code", "file1.py"])
            
            # The mock should have been called
            assert mock_check_cmd.called
            # Check that the group_by option was passed
            args, kwargs = mock_check_cmd.call_args
            assert kwargs["group_by"] == "code"
    finally:
        # Restore the original callback
        check_cmd.callback = original_callback


def test_cli_with_table_format_option():
    """Test CLI with table-format option."""
    # Create a mock for the check command
    mock_check_cmd = MagicMock()
    
    # Find the check command in the CLI group
    check_cmd = None
    for cmd_name, cmd in cli.commands.items():
        if cmd_name == "check":
            check_cmd = cmd
            break
    
    # Save the original callback
    original_callback = check_cmd.callback
    
    try:
        # Replace the callback with our mock
        check_cmd.callback = mock_check_cmd
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a dummy file
            with open("file1.py", "w") as f:
                f.write("print('hello')")
            
            result = runner.invoke(cli, ["check", "--tools", "black", "--table-format", "file1.py"])
            
            # The mock should have been called
            assert mock_check_cmd.called
            # Check that the table_format option was passed
            args, kwargs = mock_check_cmd.call_args
            assert kwargs["table_format"] == True
    finally:
        # Restore the original callback
        check_cmd.callback = original_callback 