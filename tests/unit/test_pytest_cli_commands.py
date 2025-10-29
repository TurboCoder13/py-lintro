"""Tests for pytest CLI test command."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from assertpy import assert_that
from click.testing import CliRunner

from lintro.cli_utils.commands.test import test_command, test


def test_test_command_help() -> None:
    """Test that test command shows help."""
    runner = CliRunner()
    result = runner.invoke(test_command, ["--help"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("Run tests using pytest")


def test_test_command_default_paths() -> None:
    """Test test command with default paths."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.test.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        result = runner.invoke(test_command, [])
        assert_that(mock_run.called).is_true()
        call_args = mock_run.call_args
        assert_that(call_args.kwargs["paths"]).is_equal_to(["."])
        assert_that(call_args.kwargs["tools"]).is_equal_to("pt")


def test_test_command_explicit_paths() -> None:
    """Test test command with explicit paths."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        (test_dir / "test_file.py").write_text("def test(): pass\n")
        with patch("lintro.cli_utils.commands.test.run_lint_tools_simple") as mock_run:
            mock_run.return_value = 0
            result = runner.invoke(
                test_command,
                [str(test_dir / "test_file.py")],
            )
            call_args = mock_run.call_args
            assert_that(call_args.kwargs["paths"]).contains(
                str(test_dir / "test_file.py"),
            )


def test_test_command_exclude_patterns() -> None:
    """Test test command with exclude patterns."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.test.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        result = runner.invoke(
            test_command,
            ["--exclude", "*.venv,__pycache__"],
        )
        call_args = mock_run.call_args
        assert_that(call_args.kwargs["exclude"]).is_equal_to("*.venv,__pycache__")


def test_test_command_include_venv() -> None:
    """Test test command with include-venv flag."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.test.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        result = runner.invoke(test_command, ["--include-venv"])
        call_args = mock_run.call_args
        assert_that(call_args.kwargs["include_venv"]).is_true()


def test_test_command_output_format() -> None:
    """Test test command with output format option."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.test.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        result = runner.invoke(
            test_command,
            ["--output-format", "json"],
        )
        call_args = mock_run.call_args
        assert_that(call_args.kwargs["output_format"]).is_equal_to("json")


def test_test_command_group_by() -> None:
    """Test test command with group-by option."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.test.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        result = runner.invoke(test_command, ["--group-by", "code"])
        call_args = mock_run.call_args
        assert_that(call_args.kwargs["group_by"]).is_equal_to("code")


def test_test_command_verbose() -> None:
    """Test test command with verbose flag."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.test.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        result = runner.invoke(test_command, ["--verbose"])
        call_args = mock_run.call_args
        assert_that(call_args.kwargs["verbose"]).is_true()


def test_test_command_raw_output() -> None:
    """Test test command with raw-output flag."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.test.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        result = runner.invoke(test_command, ["--raw-output"])
        call_args = mock_run.call_args
        assert_that(call_args.kwargs["raw_output"]).is_true()


def test_test_command_tool_options_without_prefix() -> None:
    """Test test command with tool options without pt: prefix."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.test.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        result = runner.invoke(
            test_command,
            ["--tool-options", "verbose=true,tb=long"],
        )
        call_args = mock_run.call_args
        tool_opts = call_args.kwargs["tool_options"]
        assert_that(tool_opts).contains("pt:verbose=true")
        assert_that(tool_opts).contains("pt:tb=long")


def test_test_command_tool_options_with_prefix() -> None:
    """Test test command with tool options already prefixed."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.test.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        result = runner.invoke(
            test_command,
            ["--tool-options", "pt:verbose=true"],
        )
        call_args = mock_run.call_args
        tool_opts = call_args.kwargs["tool_options"]
        assert_that(tool_opts).is_equal_to("pt:verbose=true")


def test_test_command_tool_options_mixed() -> None:
    """Test test command with mixed prefixed and unprefixed tool options."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.test.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        result = runner.invoke(
            test_command,
            ["--tool-options", "verbose=true,pt:tb=long"],
        )
        call_args = mock_run.call_args
        tool_opts = call_args.kwargs["tool_options"]
        assert_that(tool_opts).contains("pt:verbose=true")
        assert_that(tool_opts).contains("pt:tb=long")


def test_test_command_exit_code_success() -> None:
    """Test test command propagates success exit code."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.test.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        result = runner.invoke(test_command, [])
        assert_that(result.exit_code).is_equal_to(0)


def test_test_command_exit_code_failure() -> None:
    """Test test command propagates failure exit code."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.test.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 1
        result = runner.invoke(test_command, [])
        assert_that(result.exit_code).is_equal_to(1)


def test_test_command_combined_options() -> None:
    """Test test command with multiple options combined."""
    runner = CliRunner()
    with patch("lintro.cli_utils.commands.test.run_lint_tools_simple") as mock_run:
        mock_run.return_value = 0
        result = runner.invoke(
            test_command,
            [
                ".",
                "--exclude",
                "*.venv",
                "--include-venv",
                "--output-format",
                "markdown",
                "--group-by",
                "file",
                "--verbose",
                "--raw-output",
                "--tool-options",
                "maxfail=5",
            ],
        )
        call_args = mock_run.call_args
        assert_that(call_args.kwargs["exclude"]).is_equal_to("*.venv")
        assert_that(call_args.kwargs["include_venv"]).is_true()
        assert_that(call_args.kwargs["output_format"]).is_equal_to("markdown")
        assert_that(call_args.kwargs["group_by"]).is_equal_to("file")
        assert_that(call_args.kwargs["verbose"]).is_true()
        assert_that(call_args.kwargs["raw_output"]).is_true()


def test_test_function_no_options() -> None:
    """Test programmatic test function with no options."""
    with patch("lintro.cli_utils.commands.test.CliRunner.invoke") as mock_invoke:
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_invoke.return_value = mock_result
        result = test(
            paths=(),
            exclude=None,
            include_venv=False,
            output=None,
            output_format=None,
            group_by=None,
            verbose=False,
            tool_options=None,
        )
        assert_that(result).is_none()
        assert_that(mock_invoke.called).is_true()


def test_test_function_with_paths() -> None:
    """Test programmatic test function with paths."""
    with patch("lintro.cli_utils.commands.test.CliRunner.invoke") as mock_invoke:
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_invoke.return_value = mock_result
        test(
            paths=("tests/",),
            exclude=None,
            include_venv=False,
            output=None,
            output_format=None,
            group_by=None,
            verbose=False,
            tool_options=None,
        )
        call_args = mock_invoke.call_args
        assert_that(call_args[0][1]).contains("tests/")


def test_test_function_with_exclude() -> None:
    """Test programmatic test function with exclude patterns."""
    with patch("lintro.cli_utils.commands.test.CliRunner.invoke") as mock_invoke:
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_invoke.return_value = mock_result
        test(
            paths=(),
            exclude="*.venv",
            include_venv=False,
            output=None,
            output_format=None,
            group_by=None,
            verbose=False,
            tool_options=None,
        )
        call_args = mock_invoke.call_args
        assert_that(call_args[0][1]).contains("--exclude")
        assert_that(call_args[0][1]).contains("*.venv")


def test_test_function_with_include_venv() -> None:
    """Test programmatic test function with include-venv."""
    with patch("lintro.cli_utils.commands.test.CliRunner.invoke") as mock_invoke:
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_invoke.return_value = mock_result
        test(
            paths=(),
            exclude=None,
            include_venv=True,
            output=None,
            output_format=None,
            group_by=None,
            verbose=False,
            tool_options=None,
        )
        call_args = mock_invoke.call_args
        assert_that(call_args[0][1]).contains("--include-venv")


def test_test_function_with_output() -> None:
    """Test programmatic test function with output file."""
    with patch("lintro.cli_utils.commands.test.CliRunner.invoke") as mock_invoke:
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_invoke.return_value = mock_result
        test(
            paths=(),
            exclude=None,
            include_venv=False,
            output="/tmp/output.txt",
            output_format=None,
            group_by=None,
            verbose=False,
            tool_options=None,
        )
        call_args = mock_invoke.call_args
        assert_that(call_args[0][1]).contains("--output")
        assert_that(call_args[0][1]).contains("/tmp/output.txt")


def test_test_function_with_output_format() -> None:
    """Test programmatic test function with output format."""
    with patch("lintro.cli_utils.commands.test.CliRunner.invoke") as mock_invoke:
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_invoke.return_value = mock_result
        test(
            paths=(),
            exclude=None,
            include_venv=False,
            output=None,
            output_format="json",
            group_by=None,
            verbose=False,
            tool_options=None,
        )
        call_args = mock_invoke.call_args
        assert_that(call_args[0][1]).contains("--output-format")
        assert_that(call_args[0][1]).contains("json")


def test_test_function_with_group_by() -> None:
    """Test programmatic test function with group-by."""
    with patch("lintro.cli_utils.commands.test.CliRunner.invoke") as mock_invoke:
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_invoke.return_value = mock_result
        test(
            paths=(),
            exclude=None,
            include_venv=False,
            output=None,
            output_format=None,
            group_by="code",
            verbose=False,
            tool_options=None,
        )
        call_args = mock_invoke.call_args
        assert_that(call_args[0][1]).contains("--group-by")
        assert_that(call_args[0][1]).contains("code")


def test_test_function_with_verbose() -> None:
    """Test programmatic test function with verbose flag."""
    with patch("lintro.cli_utils.commands.test.CliRunner.invoke") as mock_invoke:
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_invoke.return_value = mock_result
        test(
            paths=(),
            exclude=None,
            include_venv=False,
            output=None,
            output_format=None,
            group_by=None,
            verbose=True,
            tool_options=None,
        )
        call_args = mock_invoke.call_args
        assert_that(call_args[0][1]).contains("--verbose")


def test_test_function_with_tool_options() -> None:
    """Test programmatic test function with tool options."""
    with patch("lintro.cli_utils.commands.test.CliRunner.invoke") as mock_invoke:
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_invoke.return_value = mock_result
        test(
            paths=(),
            exclude=None,
            include_venv=False,
            output=None,
            output_format=None,
            group_by=None,
            verbose=False,
            tool_options="maxfail=5",
        )
        call_args = mock_invoke.call_args
        assert_that(call_args[0][1]).contains("--tool-options")
        assert_that(call_args[0][1]).contains("maxfail=5")


def test_test_function_exit_code_success() -> None:
    """Test programmatic function exits with success code."""
    with patch("lintro.cli_utils.commands.test.CliRunner.invoke") as mock_invoke:
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_invoke.return_value = mock_result
        result = test(
            paths=(),
            exclude=None,
            include_venv=False,
            output=None,
            output_format=None,
            group_by=None,
            verbose=False,
            tool_options=None,
        )
        assert_that(result).is_none()


def test_test_function_exit_code_failure() -> None:
    """Test programmatic function exits with failure code."""
    with patch("lintro.cli_utils.commands.test.CliRunner.invoke") as mock_invoke:
        mock_result = Mock()
        mock_result.exit_code = 1
        mock_invoke.return_value = mock_result
        with patch("sys.exit") as mock_exit:
            test(
                paths=(),
                exclude=None,
                include_venv=False,
                output=None,
                output_format=None,
                group_by=None,
                verbose=False,
                tool_options=None,
            )
            assert_that(mock_exit.called).is_true()
