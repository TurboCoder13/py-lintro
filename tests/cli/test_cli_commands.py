"""Tests for CLI commands module.

This module contains tests for the CLI command implementations in Lintro.
"""

import pytest

from unittest.mock import patch

from lintro.cli_utils.commands.check import check_command, check
from lintro.cli_utils.commands.fmt import fmt_command, fmt
from lintro.cli_utils.commands.list_tools import list_tools_command


@pytest.fixture
def cli_runner():
    """Provide a Click CLI runner for testing.

    Returns:
        click.testing.CliRunner: CLI runner for invoking commands.
    """
    from click.testing import CliRunner

    return CliRunner()


def test_check_command_help(cli_runner):
    """Test that check command help works correctly.

    Args:
        cli_runner: Pytest fixture for CLI runner.
    """
    result = cli_runner.invoke(check_command, ["--help"])
    assert result.exit_code == 0
    assert "Check files for issues" in result.output


@patch("lintro.cli_utils.commands.check.check")
def test_check_command_invokes_check_function(mock_check, cli_runner, tmp_path):
    """Test that check command invokes the check function.

    Args:
        mock_check: Mocked check function.
        cli_runner: Pytest fixture for CLI runner.
        tmp_path: Temporary directory fixture.
    """
    mock_check.return_value = 0
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    result = cli_runner.invoke(check_command, [str(test_file)])
    assert result.exit_code == 0
    mock_check.assert_called_once()


@patch("lintro.cli_utils.commands.check.check")
def test_check_command_with_tools_option(mock_check, cli_runner, tmp_path):
    """Test check command with tools option.

    Args:
        mock_check: Mocked check function.
        cli_runner: Pytest fixture for CLI runner.
        tmp_path: Temporary directory fixture.
    """
    mock_check.return_value = 0
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    result = cli_runner.invoke(
        check_command, ["--tools", "ruff,yamllint", str(test_file)]
    )
    assert result.exit_code == 0
    mock_check.assert_called_once()


@patch("lintro.cli_utils.commands.check.check")
def test_check_command_with_output_option(mock_check, cli_runner, tmp_path):
    """Test check command with output option.

    Args:
        mock_check: Mocked check function.
        cli_runner: Pytest fixture for CLI runner.
        tmp_path: Temporary directory fixture.
    """
    mock_check.return_value = 0
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    result = cli_runner.invoke(
        check_command, ["--output", "results.txt", str(test_file)]
    )
    assert result.exit_code == 0
    mock_check.assert_called_once()


@patch("lintro.cli_utils.commands.check.check")
def test_check_command_with_format_option(mock_check, cli_runner, tmp_path):
    """Test check command with format option.

    Args:
        mock_check: Mocked check function.
        cli_runner: Pytest fixture for CLI runner.
        tmp_path: Temporary directory fixture.
    """
    mock_check.return_value = 0
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    result = cli_runner.invoke(check_command, ["--format", "json", str(test_file)])
    assert result.exit_code == 0
    mock_check.assert_called_once()


@patch("lintro.cli_utils.commands.check.check")
def test_check_command_with_verbose_option(mock_check, cli_runner, tmp_path):
    """Test check command with verbose option.

    Args:
        mock_check: Mocked check function.
        cli_runner: Pytest fixture for CLI runner.
        tmp_path: Temporary directory fixture.
    """
    mock_check.return_value = 0
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    result = cli_runner.invoke(check_command, ["--verbose", str(test_file)])
    assert result.exit_code == 0
    mock_check.assert_called_once()


def test_fmt_command_help(cli_runner):
    """Test that fmt command help works correctly.

    Args:
        cli_runner: Pytest fixture for CLI runner.
    """
    result = cli_runner.invoke(fmt_command, ["--help"])
    assert result.exit_code == 0
    assert "Fix (format) files using the specified tools." in result.output


@patch("lintro.cli_utils.commands.fmt.fmt")
def test_fmt_command_invokes_fmt_function(mock_fmt, cli_runner, tmp_path):
    """Test that fmt command invokes the fmt function.

    Args:
        mock_fmt: Mocked fmt function.
        cli_runner: Pytest fixture for CLI runner.
        tmp_path: Temporary directory fixture.
    """
    mock_fmt.return_value = 0
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    result = cli_runner.invoke(fmt_command, [str(test_file)])
    assert result.exit_code == 0
    mock_fmt.assert_called_once()


@patch("lintro.cli_utils.commands.fmt.fmt")
def test_fmt_command_with_tools_option(mock_fmt, cli_runner, tmp_path):
    """Test fmt command with tools option.

    Args:
        mock_fmt: Mocked fmt function.
        cli_runner: Pytest fixture for CLI runner.
        tmp_path: Temporary directory fixture.
    """
    mock_fmt.return_value = 0
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    result = cli_runner.invoke(
        fmt_command, ["--tools", "ruff,prettier", str(test_file)]
    )
    assert result.exit_code == 0
    mock_fmt.assert_called_once()


def test_list_tools_command_help(cli_runner):
    """Test that list-tools command help works correctly.

    Args:
        cli_runner: Pytest fixture for CLI runner.
    """
    result = cli_runner.invoke(list_tools_command, ["--help"])
    assert result.exit_code == 0
    assert "List all available tools" in result.output


@patch("lintro.cli_utils.commands.list_tools.list_tools")
def test_list_tools_command_invokes_list_tools_function(mock_list_tools, cli_runner):
    """Test that list-tools command invokes the list_tools function.

    Args:
        mock_list_tools: Mocked list_tools function.
        cli_runner: Pytest fixture for CLI runner.
    """
    mock_list_tools.return_value = 0

    result = cli_runner.invoke(list_tools_command, [])

    assert result.exit_code == 0
    mock_list_tools.assert_called_once()


@patch("lintro.cli_utils.commands.check.tool_manager")
@patch("lintro.cli_utils.commands.check.format_tool_output")
@patch("lintro.cli_utils.commands.check.print_summary")
def test_check_function_basic(
    mock_print_summary, mock_format_output, mock_tool_manager, tmp_path
):
    """Test basic check function logic.

    Args:
        mock_print_summary: Mocked print_summary function.
        mock_format_output: Mocked format_tool_output function.
        mock_tool_manager: Mocked tool_manager object.
        tmp_path: Temporary directory fixture.
    """
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    mock_tool_manager.get_tools_for_paths.return_value = []
    result = check(
        paths=[str(test_file)],
        tools=None,
        tool_options=None,
        exclude=None,
        include_venv=False,
        output=None,
        output_format="grid",
        group_by="file",
        ignore_conflicts=False,
        darglint_timeout=None,
        prettier_timeout=None,
        verbose=False,
        no_log=False,
    )
    assert result is None


@patch("lintro.cli_utils.commands.check.tool_manager")
def test_check_function_with_specific_tools(mock_tool_manager, tmp_path):
    """Test check function with specific tools.

    Args:
        mock_tool_manager: Mocked tool_manager object.
        tmp_path: Temporary directory fixture.
    """
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    mock_tool_manager.get_tools_for_paths.return_value = []
    result = check(
        paths=[str(test_file)],
        tools="ruff",
        tool_options=None,
        exclude=None,
        include_venv=False,
        output=None,
        output_format="grid",
        group_by="file",
        ignore_conflicts=False,
        darglint_timeout=None,
        prettier_timeout=None,
        verbose=False,
        no_log=False,
    )
    assert result is None


@patch("lintro.cli_utils.commands.check.tool_manager")
def test_check_function_with_tool_options(mock_tool_manager, tmp_path):
    """Test check function with tool options.

    Args:
        mock_tool_manager: Mocked tool_manager object.
        tmp_path: Temporary directory fixture.
    """
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    mock_tool_manager.get_tools_for_paths.return_value = []
    result = check(
        paths=[str(test_file)],
        tools="ruff",
        tool_options="ruff:max-line-length=100",
        exclude=None,
        include_venv=False,
        output=None,
        output_format="grid",
        group_by="file",
        ignore_conflicts=False,
        darglint_timeout=None,
        prettier_timeout=None,
        verbose=False,
        no_log=False,
    )
    assert result is None


@patch("lintro.cli_utils.commands.fmt.tool_manager")
@patch("lintro.cli_utils.commands.fmt.format_tool_output")
@patch("lintro.cli_utils.commands.fmt.print_summary")
def test_fmt_function_basic(
    mock_print_summary, mock_format_output, mock_tool_manager, tmp_path
):
    """Test basic fmt function logic.

    Args:
        mock_print_summary: Mocked print_summary function.
        mock_format_output: Mocked format_tool_output function.
        mock_tool_manager: Mocked tool_manager object.
        tmp_path: Temporary directory fixture.
    """
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    mock_tool_manager.get_tools_for_paths.return_value = []
    result = fmt(
        paths=[str(test_file)],
        tools=None,
        tool_options=None,
        exclude=None,
        include_venv=False,
        output=None,
        output_format="grid",
        group_by="auto",
        ignore_conflicts=False,
        darglint_timeout=None,
        prettier_timeout=None,
        verbose=False,
        debug_file=None,
    )
    assert result is None
