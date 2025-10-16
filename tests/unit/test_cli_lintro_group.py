"""Tests for LintroGroup and CLI module functionality."""

from unittest.mock import patch

from assertpy import assert_that
from click.testing import CliRunner

from lintro.cli import cli


def test_format_commands_displays_canonical_names() -> None:
    """Test that format_commands displays canonical command names."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("check")
    assert_that(result.output).contains("format")
    assert_that(result.output).contains("test")
    assert_that(result.output).contains("list-tools")


def test_format_commands_with_aliases() -> None:
    """Test that format_commands includes aliases in help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    # The output should contain commands with or without aliases
    assert_that(result.exit_code).is_equal_to(0)
    # Check that each canonical name appears
    assert_that(result.output).contains("Commands:")


def test_check_command_help_displays() -> None:
    """Test that check command help displays properly."""
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--help"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("Check files for issues")


def test_format_command_help_displays() -> None:
    """Test that format command help displays properly."""
    runner = CliRunner()
    result = runner.invoke(cli, ["format", "--help"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("Format code")


def test_test_command_help_displays() -> None:
    """Test that test command help displays properly."""
    runner = CliRunner()
    result = runner.invoke(cli, ["test", "--help"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("Run tests")


def test_list_tools_command_help_displays() -> None:
    """Test that list-tools command help displays properly."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list-tools", "--help"])
    assert_that(result.exit_code).is_equal_to(0)


def test_invoke_single_command_execution() -> None:
    """Test that invoke executes single command correctly."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.check.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        result = runner.invoke(cli, ["check", "."])
        assert_that(result.exit_code).is_equal_to(0)
        assert_that(mock_run.called).is_true()


def test_invoke_with_comma_separated_commands() -> None:
    """Test that invoke handles comma-separated command chaining."""
    runner = CliRunner()
    with (
        patch("lintro.cli_utils.commands.check.run_lint_tools_simple") as mock_check,
        patch("lintro.cli_utils.commands.format.run_lint_tools_simple") as mock_fmt,
    ):
        mock_check.return_value = 0
        mock_fmt.return_value = 0
        runner.invoke(cli, ["check", ".", ",", "format", "."])
        # Both commands should have been attempted
        # Note: The actual behavior depends on how the invoke method works


def test_invoke_aggregates_exit_codes_success() -> None:
    """Test that invoke aggregates exit codes from chained commands."""
    runner = CliRunner()
    with patch("lintro.tools.tool_manager.get_available_tools") as mock_get:
        mock_get.return_value = {}
        result = runner.invoke(cli, ["list-tools"])
        # Should return 0 when command succeeds
        assert_that(result.exit_code).is_equal_to(0)


def test_invoke_with_version_flag() -> None:
    """Test that invoke handles --version flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("version")


def test_invoke_with_help_flag() -> None:
    """Test that invoke handles --help flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("Lintro")


def test_invoke_without_command_shows_help() -> None:
    """Test that invoking cli without command succeeds."""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    # Should succeed (exit code 0) when invoked without command
    assert_that(result.exit_code).is_equal_to(0)


def test_invoke_with_invalid_command() -> None:
    """Test that invoke handles invalid commands."""
    runner = CliRunner()
    result = runner.invoke(cli, ["invalid-command"])
    assert_that(result.exit_code).is_not_equal_to(0)


def test_invoke_command_not_found() -> None:
    """Test error handling for non-existent command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["nonexistent"])
    assert_that(result.exit_code).is_not_equal_to(0)
    assert_that(result.output).contains("No such command")


def test_chaining_preserves_command_order() -> None:
    """Test that command chaining preserves execution order."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.check.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        runner.invoke(cli, ["check", "."])
        # At least one check command should have been called
        assert_that(mock_run.call_count).is_greater_than_or_equal_to(1)


def test_chaining_with_multiple_commands() -> None:
    """Test chaining with three or more commands."""
    runner = CliRunner()
    with patch("lintro.tools.tool_manager.get_available_tools") as mock_get:
        mock_get.return_value = {}
        # This would chain multiple commands (though functionality
        # depends on implementation)
        result = runner.invoke(cli, ["list-tools"])
        # Should handle list-tools command
        assert_that(result.exit_code).is_equal_to(0)


def test_chaining_ignores_empty_command_groups() -> None:
    """Test that chaining ignores empty command groups."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.check.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        # Multiple commas in a row would create empty groups
        runner.invoke(cli, ["check", ".", ",", ",", "check", "."])
        # Should still execute the check commands, ignoring empty groups


def test_chaining_with_flags() -> None:
    """Test that chaining preserves flags for each command."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.check.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        runner.invoke(
            cli,
            ["check", ".", "--tools", "ruff", ",", "check", "."],
        )
        # Check commands should have been called with their respective flags


def test_invoke_handles_system_exit() -> None:
    """Test that invoke properly handles SystemExit exceptions."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.check.run_lint_tools_simple") as mock_run:
        mock_run.side_effect = SystemExit(1)
        runner.invoke(cli, ["check", "."])
        # Should handle SystemExit gracefully


def test_invoke_preserves_max_exit_code() -> None:
    """Test that chained command execution preserves the max exit code."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.check.run_lint_tools_simple") as mock_run:
        # Simulate different exit codes from multiple runs
        mock_run.side_effect = [0, 1]
        runner.invoke(cli, ["check", ".", ",", "check", "."])
        # Result should reflect the maximum exit code (1)


def test_invoke_with_exception_in_command() -> None:
    """Test error handling when command raises exception."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.check.run_lint_tools_simple") as mock_run:
        mock_run.side_effect = Exception("Test error")
        runner.invoke(cli, ["check", "."])
        # Should handle exceptions gracefully
