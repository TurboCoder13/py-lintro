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
    result = runner.invoke(cli, ["test", "--help"])
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
    result = runner.invoke(cli, ["tst", "--help"])
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


def test_test_command_help() -> None:
    """Test that test command displays help."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, ["test", "--help"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("Run tests")


def test_test_command_alias() -> None:
    """Test that 'tst' alias works for test command."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, ["tst", "--help"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("Run tests")


def test_command_chaining_basic() -> None:
    """Test basic command chaining syntax recognition."""
    from unittest.mock import patch

    from click.testing import CliRunner

    runner = CliRunner()
    # Patch both format and check commands to prevent real tools from executing
    with (
        patch("lintro.cli_utils.commands.format.run_lint_tools_simple") as mock_fmt,
        patch("lintro.cli_utils.commands.check.run_lint_tools_simple") as mock_chk,
    ):
        mock_fmt.return_value = 0
        mock_chk.return_value = 0
        # Test that chaining syntax is accepted (should parse correctly)
        result = runner.invoke(cli, ["fmt", ",", "chk"])
        # We expect this to succeed with mocked runners, not parsing errors
        assert_that(result.output).does_not_contain("Error: unexpected argument")


def test_pytest_excluded_from_check_help() -> None:
    """Test that pytest is excluded from available tools in check command."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--help"])
    assert_that(result.exit_code).is_equal_to(0)
    # The help should not mention pytest as an available tool for check
    assert_that(result.output).does_not_contain("pytest")


def test_pytest_excluded_from_fmt_help() -> None:
    """Test that pytest is excluded from available tools in format command."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, ["format", "--help"])
    assert_that(result.exit_code).is_equal_to(0)
    # The help should not mention pytest as an available tool for format
    assert_that(result.output).does_not_contain("pytest")
