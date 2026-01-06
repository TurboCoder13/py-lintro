"""Unit tests for pytest programmatic API."""

from __future__ import annotations

from unittest.mock import Mock, patch

from assertpy import assert_that

from lintro.cli_utils.commands.test import test


def test_test_function_with_default_options() -> None:
    """Test programmatic test function with explicit default options."""
    with patch("lintro.cli_utils.commands.test.CliRunner.invoke") as mock_invoke:
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_invoke.return_value = mock_result
        test(
            paths=(),
            exclude=None,
            include_venv=False,
            output=None,
            output_format="grid",
            group_by="file",
            verbose=False,
            tool_options=None,
        )
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
            output_format="grid",
            group_by="file",
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
            output_format="grid",
            group_by="file",
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
            output_format="grid",
            group_by="file",
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
            output_format="grid",
            group_by="file",
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
            group_by="file",
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
            output_format="grid",
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
            output_format="grid",
            group_by="file",
            verbose=True,
            tool_options=None,
        )
        call_args = mock_invoke.call_args
        assert_that(call_args[0][1]).contains("--verbose")


def test_test_function_with_raw_output() -> None:
    """Test programmatic test function with raw-output flag."""
    with patch("lintro.cli_utils.commands.test.CliRunner.invoke") as mock_invoke:
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_invoke.return_value = mock_result
        test(
            paths=(),
            exclude=None,
            include_venv=False,
            output=None,
            output_format="grid",
            group_by="file",
            verbose=False,
            raw_output=True,
            tool_options=None,
        )
        call_args = mock_invoke.call_args
        assert_that(call_args[0][1]).contains("--raw-output")


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
            output_format="grid",
            group_by="file",
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
        # test() returns None on success, no assignment needed
        test(
            paths=(),
            exclude=None,
            include_venv=False,
            output=None,
            output_format="grid",
            group_by="file",
            verbose=False,
            tool_options=None,
        )
        assert_that(mock_invoke.called).is_true()


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
                output_format="grid",
                group_by="file",
                verbose=False,
                tool_options=None,
            )
            mock_exit.assert_called_once_with(1)
