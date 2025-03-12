"""Tests for Lintro CLI."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from lintro.cli import cli


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_version(runner):
    """Test the --version option."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert (
        "version" in result.output
    )  # Just check for "version" instead of specific format


@patch("lintro.tools.AVAILABLE_TOOLS")
def test_list_tools(
    mock_tools,
    runner,
):
    """Test the list-tools command."""
    mock_tools.items.return_value = [
        ("black", MagicMock(name="black", description="Black formatter", can_fix=True)),
        (
            "flake8",
            MagicMock(name="flake8", description="Flake8 linter", can_fix=False),
        ),
    ]

    result = runner.invoke(cli, ["list-tools"])

    assert result.exit_code == 0
    assert "black" in result.output
    assert "flake8" in result.output
    assert "Tools that can fix issues" in result.output
    assert "Tools that can only check for issues" in result.output


@patch("lintro.cli.CHECK_TOOLS")
@patch("os.getcwd")
def test_check_no_path(
    mock_getcwd,
    mock_tools,
    runner,
):
    """Test the check command with no path argument."""
    mock_getcwd.return_value = "/test/path"
    mock_tool = MagicMock()
    mock_tool.check.return_value = (True, "No issues found")
    mock_tools.items.return_value = [("test-tool", mock_tool)]

    # Mock print_summary to avoid errors
    with patch("lintro.cli.print_summary"):
        # Mock set_options method
        mock_tool.set_options = MagicMock()

        # Mock count_issues and format_tool_output
        with patch("lintro.cli.count_issues", return_value=0):
            with patch(
                "lintro.cli.format_tool_output", return_value="Formatted output"
            ):
                result = runner.invoke(cli, ["check"])

                assert result.exit_code == 0
                mock_tool.check.assert_called_once_with(["/test/path"])
                assert "Formatted output" in result.output


@patch("lintro.cli.FIX_TOOLS")
def test_fmt_with_path(
    mock_tools,
    runner,
):
    """Test the fmt command with a path argument."""
    mock_tool = MagicMock()
    mock_tool.fix.return_value = (True, "Fixed issues")
    mock_tools.items.return_value = [("test-tool", mock_tool)]

    # Mock print_summary to avoid errors
    with patch("lintro.cli.print_summary"):
        with runner.isolated_filesystem():
            with open("test_file.py", "w") as f:
                f.write("# Test file")

            # Mock set_options method
            mock_tool.set_options = MagicMock()

            # Mock count_issues and format_tool_output
            with patch("lintro.cli.count_issues", return_value=0):
                with patch(
                    "lintro.cli.format_tool_output", return_value="Formatted output"
                ):
                    result = runner.invoke(cli, ["fmt", "test_file.py"])

                    assert result.exit_code == 0
                    mock_tool.fix.assert_called_once_with(["test_file.py"])
                    assert "Formatted output" in result.output


@patch("lintro.cli.FIX_TOOLS")
def test_fmt_with_specific_tools(
    mock_tools,
    runner,
):
    """Test the fmt command with specific tools."""
    mock_black = MagicMock()
    mock_black.fix.return_value = (True, "Black fixed issues")
    mock_isort = MagicMock()
    mock_isort.fix.return_value = (True, "isort fixed issues")

    mock_tools.items.return_value = [
        ("black", mock_black),
        ("isort", mock_isort),
    ]

    # Mock print_summary to avoid errors
    with patch("lintro.cli.print_summary"):
        with runner.isolated_filesystem():
            with open("test_file.py", "w") as f:
                f.write("# Test file")

            # Mock set_options method
            mock_black.set_options = MagicMock()
            mock_isort.set_options = MagicMock()

            # Mock count_issues and format_tool_output
            with patch("lintro.cli.count_issues", return_value=0):
                with patch(
                    "lintro.cli.format_tool_output", return_value="Formatted output"
                ):
                    result = runner.invoke(
                        cli, ["fmt", "--tools", "black", "test_file.py"]
                    )

                    assert result.exit_code == 0
                    mock_black.fix.assert_called_once_with(["test_file.py"])
                    mock_isort.fix.assert_not_called()
