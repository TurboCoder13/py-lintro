"""Tests for the CLI module.

This module contains tests for the main CLI entry points in Lintro.
"""

import pytest
from unittest.mock import patch

from lintro.cli import cli, main


@pytest.fixture
def cli_runner():
    """Provide a Click CLI runner for testing.

    Returns:
        click.testing.CliRunner: CLI runner for invoking commands.
    """
    from click.testing import CliRunner

    return CliRunner()


@pytest.mark.cli
def test_cli_help(cli_runner):
    """Test that CLI help works correctly.

    Args:
        cli_runner: Pytest fixture for CLI runner.
    """
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert (
        "Lintro: Unified CLI for code formatting, linting, and quality assurance."
        in result.output
    )
    assert "check / chk" in result.output
    assert "format / fmt" in result.output
    assert "list-tools / ls" in result.output


@pytest.mark.cli
def test_cli_version(cli_runner):
    """Test that CLI version works correctly.

    Args:
        cli_runner: Pytest fixture for CLI runner.
    """
    result = cli_runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()


@pytest.mark.cli
def test_cli_commands_registered():
    """Test that all commands are properly registered."""
    # Get all command names from the CLI group
    command_names = list(cli.commands.keys())

    # Check that all expected commands are present
    expected_commands = ["check", "format", "chk", "fmt", "list-tools", "ls"]
    for cmd in expected_commands:
        assert cmd in command_names


@pytest.mark.cli
def test_main_function():
    """Test the main function entry point."""
    with patch("lintro.cli.cli") as mock_cli:
        main()
        mock_cli.assert_called_once()


@pytest.mark.cli
def test_cli_command_aliases(cli_runner):
    """Test that command aliases work correctly.

    Args:
        cli_runner: Pytest fixture for CLI runner.
    """
    # Test that 'format' alias works
    result = cli_runner.invoke(cli, ["format", "--help"])
    assert result.exit_code == 0
    assert "Format code using configured formatting tools" in result.output

    # Test that 'chk' alias works
    result = cli_runner.invoke(cli, ["chk", "--help"])
    assert result.exit_code == 0
    assert "Check code quality using configured linting tools" in result.output

    # Test that 'ls' alias works
    result = cli_runner.invoke(cli, ["ls", "--help"])
    assert result.exit_code == 0
    assert "List all available tools" in result.output


@pytest.mark.cli
def test_cli_with_no_args(cli_runner):
    """Test CLI behavior with no arguments.

    Args:
        cli_runner: Pytest fixture for CLI runner.
    """
    result = cli_runner.invoke(cli, [])
    # CLI with no args returns empty output with exit code 0
    assert result.exit_code == 0
    # The CLI doesn't show help by default when called with no args
    assert result.output == ""
