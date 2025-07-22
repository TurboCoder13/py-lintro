"""Tests for CLI commands."""

import pytest
from unittest.mock import patch

from lintro.cli_utils.commands.check import check
from lintro.cli_utils.commands.format import format_code
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
    """Test that check command shows help.

    Args:
        cli_runner: Pytest fixture for CLI runner.
    """
    result = cli_runner.invoke(check, ["--help"])
    assert result.exit_code == 0
    assert "Check code quality using configured linting tools" in result.output


@patch("lintro.cli_utils.commands.check.run_lint_tools_simple")
def test_check_command_invokes_check_function(mock_check, cli_runner, tmp_path):
    """Test that check command invokes the check function.

    Args:
        mock_check: Mock object for the check function.
        cli_runner: Pytest fixture for CLI runner.
        tmp_path: Pytest temporary path fixture.
    """
    mock_check.return_value = 0  # Success
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    result = cli_runner.invoke(check, [str(test_file)])
    assert result.exit_code == 0
    mock_check.assert_called_once()


@patch("lintro.cli_utils.commands.check.run_lint_tools_simple")
def test_check_command_with_tools_option(mock_check, cli_runner, tmp_path):
    """Test check command with tools option.

    Args:
        mock_check: Mock object for the check function.
        cli_runner: Pytest fixture for CLI runner.
        tmp_path: Pytest temporary path fixture.
    """
    mock_check.return_value = 0  # Success
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    result = cli_runner.invoke(check, ["--tools", "ruff,yamllint", str(test_file)])
    assert result.exit_code == 0


@patch("lintro.cli_utils.commands.check.run_lint_tools_simple")
def test_check_command_with_verbose_option(mock_check, cli_runner, tmp_path):
    """Test check command with verbose option.

    Args:
        mock_check: Mock object for the check function.
        cli_runner: Pytest fixture for CLI runner.
        tmp_path: Pytest temporary path fixture.
    """
    mock_check.return_value = 0  # Success
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    result = cli_runner.invoke(check, ["--verbose", str(test_file)])
    assert result.exit_code == 0
    mock_check.assert_called_once()


def test_fmt_command_help(cli_runner):
    """Test that fmt command shows help.

    Args:
        cli_runner: Pytest fixture for CLI runner.
    """
    result = cli_runner.invoke(format_code, ["--help"])
    assert result.exit_code == 0
    assert "Format code using configured formatting tools" in result.output


@patch("lintro.cli_utils.commands.format.run_lint_tools_simple")
def test_fmt_command_invokes_fmt_function(mock_fmt, cli_runner, tmp_path):
    """Test that fmt command invokes the fmt function.

    Args:
        mock_fmt: Mock object for the fmt function.
        cli_runner: Pytest fixture for CLI runner.
        tmp_path: Pytest temporary path fixture.
    """
    mock_fmt.return_value = 0  # Success
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    result = cli_runner.invoke(format_code, [str(test_file)])
    assert result.exit_code == 0
    mock_fmt.assert_called_once()


@patch("lintro.cli_utils.commands.format.run_lint_tools_simple")
def test_fmt_command_with_tools_option(mock_fmt, cli_runner, tmp_path):
    """Test fmt command with tools option.

    Args:
        mock_fmt: Mock object for the fmt function.
        cli_runner: Pytest fixture for CLI runner.
        tmp_path: Pytest temporary path fixture.
    """
    mock_fmt.return_value = 0  # Success
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    result = cli_runner.invoke(
        format_code, ["--tools", "ruff,prettier", str(test_file)]
    )
    assert result.exit_code == 0


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


# Remove all obsolete function-level tests that call check() or fmt() with output, output_format, darglint_timeout, or prettier_timeout.
# Add a new integration test for the output manager via the CLI.


def test_cli_creates_output_manager_files(tmp_path):
    """Test that CLI creates output manager files.

    This is an integration test that checks the full CLI process.
    """
    import os
    from pathlib import Path
    from lintro.utils.tool_executor import run_lint_tools_simple
    
    # Create a test Python file
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello world')")
    
    # Change to the temp directory so output files are created there
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Run the tool executor which should create output files
        run_lint_tools_simple(
            action="check",
            tools="ruff",
            tool_options=None,
            paths=[str(test_file)],
            exclude=None,
            include_venv=False,
            group_by="auto",
            output_format="grid",
            verbose=False
        )
        
        # Check that output directory and files were created
        lintro_dir = tmp_path / ".lintro"
        assert lintro_dir.exists(), "Output directory should be created"
        
        # Find the run directory (has timestamp format)
        run_dirs = [d for d in lintro_dir.iterdir() if d.is_dir() and d.name.startswith("run-")]
        assert len(run_dirs) >= 1, "At least one run directory should be created"
        
        run_dir = run_dirs[0]
        
        # Check that expected output files were created
        expected_files = ["console.log", "debug.log", "report.md", "report.html", "summary.csv"]
        for expected_file in expected_files:
            file_path = run_dir / expected_file
            assert file_path.exists(), f"{expected_file} should be created"
            assert file_path.stat().st_size > 0, f"{expected_file} should not be empty"
            
    finally:
        os.chdir(old_cwd)
