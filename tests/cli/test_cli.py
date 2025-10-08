"""Tests for CLI module."""

import subprocess
import sys
from unittest.mock import patch

from assertpy import assert_that

from lintro.cli import cli


def test_cli_help() -> None:
    """Test that CLI shows help."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("Lintro")


def test_cli_version() -> None:
    """Test that CLI shows version."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output.lower()).contains("version")


def test_cli_commands_registered() -> None:
    """Test that all commands are registered."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--help"])
    assert_that(result.exit_code).is_equal_to(0)
    result = runner.invoke(cli, ["format", "--help"])
    assert_that(result.exit_code).is_equal_to(0)
    result = runner.invoke(cli, ["list-tools", "--help"])
    assert_that(result.exit_code).is_equal_to(0)


def test_main_function() -> None:
    """Test the main function."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("Lintro")


def test_cli_command_aliases() -> None:
    """Test that command aliases work."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, ["chk", "--help"])
    assert_that(result.exit_code).is_equal_to(0)
    result = runner.invoke(cli, ["fmt", "--help"])
    assert_that(result.exit_code).is_equal_to(0)
    result = runner.invoke(cli, ["ls", "--help"])
    assert_that(result.exit_code).is_equal_to(0)


def test_cli_with_no_args() -> None:
    """Test CLI with no arguments."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).is_equal_to("")


def test_main_module_execution() -> None:
    """Test that __main__.py can be executed directly."""
    with patch.object(sys, "argv", ["lintro", "--help"]):
        import lintro.__main__

        assert_that(lintro.__main__).is_not_none()


def test_main_module_as_script() -> None:
    """Test that __main__.py works when run as a script."""
    result = subprocess.run(
        [sys.executable, "-m", "lintro", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert_that(result.returncode).is_equal_to(0)
    assert_that(result.stdout).contains("Lintro")
