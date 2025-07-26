"""Tests for CLI module."""

import subprocess
import sys
from unittest.mock import patch

from lintro.cli import cli


def test_cli_help():
    """Test that CLI shows help."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Lintro" in result.output


def test_cli_version():
    """Test that CLI shows version."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()


def test_cli_commands_registered():
    """Test that all commands are registered."""
    from click.testing import CliRunner

    runner = CliRunner()

    # Test check command
    result = runner.invoke(cli, ["check", "--help"])
    assert result.exit_code == 0

    # Test format command
    result = runner.invoke(cli, ["format", "--help"])
    assert result.exit_code == 0

    # Test list-tools command
    result = runner.invoke(cli, ["list-tools", "--help"])
    assert result.exit_code == 0


def test_main_function():
    """Test the main function."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Lintro" in result.output


def test_cli_command_aliases():
    """Test that command aliases work."""
    from click.testing import CliRunner

    runner = CliRunner()

    # Test chk alias
    result = runner.invoke(cli, ["chk", "--help"])
    assert result.exit_code == 0

    # Test fmt alias
    result = runner.invoke(cli, ["fmt", "--help"])
    assert result.exit_code == 0

    # Test ls alias
    result = runner.invoke(cli, ["ls", "--help"])
    assert result.exit_code == 0


def test_cli_with_no_args():
    """Test CLI with no arguments."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    # CLI with no args returns empty output (no command specified)
    assert result.output == ""


def test_main_module_execution():
    """Test that __main__.py can be executed directly."""
    # Test that the module can be imported and executed
    with patch.object(sys, "argv", ["lintro", "--help"]):
        # This should not raise an exception
        import lintro.__main__

        # The module should be importable
        assert lintro.__main__ is not None


def test_main_module_as_script():
    """Test that __main__.py works when run as a script."""
    # Test running the module directly
    result = subprocess.run(
        [sys.executable, "-m", "lintro", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "Lintro" in result.stdout
