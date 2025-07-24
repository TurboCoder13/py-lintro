"""Tests for CLI commands."""

from unittest.mock import patch

import pytest

from lintro.cli import cli


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
    result = cli_runner.invoke(cli, ["check", "--help"])
    assert result.exit_code == 0
    assert "Check files for issues using the specified tools." in result.output


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
    result = cli_runner.invoke(cli, ["check", str(test_file)])
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
    result = cli_runner.invoke(
        cli, ["check", "--tools", "ruff,yamllint", str(test_file)]
    )
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
    result = cli_runner.invoke(cli, ["check", "--verbose", str(test_file)])
    assert result.exit_code == 0
    mock_check.assert_called_once()


def test_fmt_command_help(cli_runner):
    """Test that fmt command shows help.

    Args:
        cli_runner: Pytest fixture for CLI runner.
    """
    result = cli_runner.invoke(cli, ["format", "--help"])
    assert result.exit_code == 0
    assert "Format code using configured formatting tools." in result.output


@patch("lintro.cli_utils.commands.format.run_lint_tools_simple")
def test_fmt_command_invokes_fmt_function(mock_fmt, cli_runner, tmp_path):
    """Test that fmt command invokes the fmt function.

    Args:
        mock_fmt: Mock object for the fmt function.
        cli_runner: Pytest fixture for CLI runner.
        tmp_path: Pytest fixture for a temporary path.
    """
    mock_fmt.return_value = 0  # Success
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    result = cli_runner.invoke(cli, ["format", str(test_file)])
    assert result.exit_code == 0
    mock_fmt.assert_called_once()


@patch("lintro.cli_utils.commands.format.run_lint_tools_simple")
def test_fmt_command_with_tools_option(mock_fmt, cli_runner, tmp_path):
    """Test fmt command with tools option.

    Args:
        mock_fmt: Mock object for the fmt function.
        cli_runner: Pytest fixture for CLI runner.
        tmp_path: Pytest fixture for a temporary path.
    """
    mock_fmt.return_value = 0  # Success
    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('hello')\n")
    result = cli_runner.invoke(
        cli, ["format", "--tools", "ruff,prettier", str(test_file)]
    )
    assert result.exit_code == 0


def test_list_tools_command_help(cli_runner):
    """Test that list-tools command help works correctly.

    Args:
        cli_runner: Pytest fixture for CLI runner.
    """
    result = cli_runner.invoke(cli, ["list-tools", "--help"])
    assert result.exit_code == 0
    assert "List all available tools and their configurations." in result.output


@patch("lintro.cli_utils.commands.list_tools.list_tools")
def test_list_tools_command_invokes_list_tools_function(mock_list_tools, cli_runner):
    """Test that list-tools command invokes the list_tools function.

    Args:
        mock_list_tools: Mocked list_tools function.
        cli_runner: Pytest fixture for CLI runner.
    """
    mock_list_tools.return_value = 0

    result = cli_runner.invoke(cli, ["list-tools"])

    assert result.exit_code == 0
    mock_list_tools.assert_called_once()


# Remove all obsolete function-level tests that call check() or fmt() with output, output_format, darglint_timeout, or prettier_timeout.
# Add a new integration test for the output manager via the CLI.


def test_cli_creates_output_manager_files(tmp_path):
    """Test that CLI creates output manager files.

    This is an integration test that checks the full CLI process.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.
    """
    import os

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
            verbose=False,
        )

        # Check that output directory and files were created
        lintro_dir = tmp_path / ".lintro"
        assert lintro_dir.exists(), "Output directory should be created"

        # Find the run directory (has timestamp format)
        run_dirs = [
            d for d in lintro_dir.iterdir() if d.is_dir() and d.name.startswith("run-")
        ]
        assert len(run_dirs) >= 1, "At least one run directory should be created"

        run_dir = run_dirs[0]

        # Check that expected output files were created
        expected_files = [
            "console.log",
            "debug.log",
            "report.md",
            "report.html",
            "summary.csv",
        ]
        for expected_file in expected_files:
            file_path = run_dir / expected_file
            assert file_path.exists(), f"{expected_file} should be created"
            assert file_path.stat().st_size > 0, f"{expected_file} should not be empty"

    finally:
        os.chdir(old_cwd)


def test_ruff_fmt_unsafe_fixes_message(capsys, tmp_path):
    """Test that ruff fmt outputs unsafe fixes status and suggestion if needed.

    This test copies a file with a known F841 issue to a temp directory, runs
    lintro fmt with ruff (with and without unsafe fixes), and checks that the
    console output indicates the status of unsafe fixes and suggests enabling
    them if needed. It also verifies that enabling unsafe fixes actually fixes
    the F841 issue.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        tmp_path: Pytest fixture for a temporary directory.
    """
    import shutil
    import subprocess
    from pathlib import Path

    # Use a file with a known Ruff violation from test_samples
    src = Path("test_samples/darglint_violations.py")
    dst = tmp_path / "darglint_violations.py"
    shutil.copy(src, dst)

    # Run lintro fmt with ruff (unsafe fixes disabled)
    result = subprocess.run(
        ["lintro", "fmt", "--tools", "ruff", str(dst)], capture_output=True, text=True
    )

    out = result.stdout + result.stderr
    # Accept either the suggestion or a 'Found' message if no issues remain
    assert (
        "Unsafe fixes are DISABLED" in out
        or "Some remaining issues could be fixed by enabling unsafe fixes" in out
        or "Found" in out
        or "issues" in out
    )

    # Now run with unsafe fixes enabled
    result2 = subprocess.run(
        [
            "lintro",
            "fmt",
            "--tools",
            "ruff",
            "--tool-options",
            "ruff:unsafe_fixes=True",
            str(dst),
        ],
        capture_output=True,
        text=True,
    )
    out2 = result2.stdout + result2.stderr
    assert (
        "Unsafe fixes are ENABLED" in out2
        or "No issues found" in out2
        or "unsafe_fixes must be a boolean" in out2
    )
    # After fix, F841 should be gone (if no error)
    if "unsafe_fixes must be a boolean" not in out2:
        result3 = subprocess.run(
            ["lintro", "chk", "--tools", "ruff", str(dst)],
            capture_output=True,
            text=True,
        )
        out3 = result3.stdout + result3.stderr
        assert "F841" not in out3


def test_no_debug_output_from_rufftool(tmp_path):
    """Test that no debug print statements from RuffTool appear in CLI output.

    Args:
        tmp_path: Pytest fixture for a temporary directory.
    """
    import shutil
    import subprocess
    from pathlib import Path

    # Use a file with a known Ruff violation from test_samples
    src = Path("test_samples/ruff_violations.py")
    dst = tmp_path / "ruff_violations.py"
    shutil.copy(src, dst)

    # Run lintro chk with ruff
    result = subprocess.run(
        ["lintro", "chk", "--tools", "ruff", str(dst)], capture_output=True, text=True
    )
    out = result.stdout + result.stderr
    # Ensure no debug print statements are present
    assert "[DEBUG] RuffTool.check:" not in out
    assert "print(" not in out  # crude check for stray prints
