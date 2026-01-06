"""Unit tests for YamllintRunner implementation."""

from __future__ import annotations

import errno
import subprocess
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from lintro.models.core.tool_result import ToolResult
from lintro.tools.implementations.yamllint_runner import YamllintRunner


@pytest.fixture
def runner() -> YamllintRunner:
    """Create a YamllintRunner instance for testing.

    Returns:
        YamllintRunner instance for testing.
    """
    return YamllintRunner()


# --- _process_yaml_file tests ---


def test_process_yaml_file_successful_no_issues(runner: YamllintRunner) -> None:
    """Test processing a file with no issues.

    Args:
        runner: YamllintRunner instance for testing.
    """
    with (
        patch.object(runner, "get_cwd", return_value="/tmp"),
        patch.object(runner, "_get_executable_command", return_value=["yamllint"]),
        patch.object(runner, "_find_yamllint_config", return_value=None),
        patch.object(runner, "_run_subprocess", return_value=(True, "")),
        patch(
            "lintro.tools.implementations.yamllint_runner.parse_yamllint_output",
            return_value=[],
        ),
    ):
        result = runner._process_yaml_file("test.yaml", timeout=30)

        issues_count, issues, skipped, exec_fail, success, should_continue = result
        assert_that(issues_count).is_equal_to(0)
        assert_that(issues).is_empty()
        assert_that(skipped).is_false()
        assert_that(exec_fail).is_false()
        assert_that(success).is_true()
        assert_that(should_continue).is_false()


def test_process_yaml_file_with_issues(runner: YamllintRunner) -> None:
    """Test processing a file with lint issues.

    Args:
        runner: YamllintRunner instance for testing.
    """
    mock_issue = MagicMock()
    with (
        patch.object(runner, "get_cwd", return_value="/tmp"),
        patch.object(runner, "_get_executable_command", return_value=["yamllint"]),
        patch.object(runner, "_find_yamllint_config", return_value=None),
        patch.object(
            runner,
            "_run_subprocess",
            return_value=(False, "test.yaml:1:1: error: msg"),
        ),
        patch(
            "lintro.tools.implementations.yamllint_runner.parse_yamllint_output",
            return_value=[mock_issue],
        ),
    ):
        result = runner._process_yaml_file("test.yaml", timeout=30)

        issues_count, issues, skipped, exec_fail, success, should_continue = result
        assert_that(issues_count).is_equal_to(1)
        assert_that(len(issues)).is_equal_to(1)
        assert_that(success).is_false()


def test_process_yaml_file_timeout(runner: YamllintRunner) -> None:
    """Test handling of subprocess timeout.

    Args:
        runner: YamllintRunner instance for testing.
    """
    with (
        patch.object(runner, "get_cwd", return_value="/tmp"),
        patch.object(runner, "_get_executable_command", return_value=["yamllint"]),
        patch.object(runner, "_find_yamllint_config", return_value=None),
        patch.object(
            runner,
            "_run_subprocess",
            side_effect=subprocess.TimeoutExpired(cmd="yamllint", timeout=30),
        ),
    ):
        result = runner._process_yaml_file("test.yaml", timeout=30)

        issues_count, issues, skipped, exec_fail, success, should_continue = result
        assert_that(issues_count).is_equal_to(0)
        assert_that(skipped).is_true()
        assert_that(exec_fail).is_true()
        assert_that(success).is_false()


def test_process_yaml_file_not_found(runner: YamllintRunner) -> None:
    """Test handling of missing file.

    Args:
        runner: YamllintRunner instance for testing.
    """
    with (
        patch.object(runner, "get_cwd", return_value="/tmp"),
        patch.object(runner, "_get_executable_command", return_value=["yamllint"]),
        patch.object(runner, "_find_yamllint_config", return_value=None),
        patch.object(runner, "_run_subprocess", side_effect=FileNotFoundError()),
    ):
        result = runner._process_yaml_file("missing.yaml", timeout=30)

        issues_count, issues, skipped, exec_fail, success, should_continue = result
        assert_that(issues_count).is_equal_to(0)
        assert_that(success).is_true()
        assert_that(should_continue).is_true()


def test_process_yaml_file_os_error_enoent(runner: YamllintRunner) -> None:
    """Test handling of ENOENT OS error.

    Args:
        runner: YamllintRunner instance for testing.
    """
    os_error = OSError(errno.ENOENT, "No such file")
    with (
        patch.object(runner, "get_cwd", return_value="/tmp"),
        patch.object(runner, "_get_executable_command", return_value=["yamllint"]),
        patch.object(runner, "_find_yamllint_config", return_value=None),
        patch.object(runner, "_run_subprocess", side_effect=os_error),
    ):
        result = runner._process_yaml_file("test.yaml", timeout=30)

        _, _, _, _, success, should_continue = result
        assert_that(success).is_true()
        assert_that(should_continue).is_true()


def test_process_yaml_file_other_os_error(runner: YamllintRunner) -> None:
    """Test handling of other OS errors.

    Args:
        runner: YamllintRunner instance for testing.
    """
    os_error = OSError(errno.EPERM, "Permission denied")
    with (
        patch.object(runner, "get_cwd", return_value="/tmp"),
        patch.object(runner, "_get_executable_command", return_value=["yamllint"]),
        patch.object(runner, "_find_yamllint_config", return_value=None),
        patch.object(runner, "_run_subprocess", side_effect=os_error),
    ):
        result = runner._process_yaml_file("test.yaml", timeout=30)

        _, _, _, exec_fail, success, _ = result
        assert_that(exec_fail).is_true()
        assert_that(success).is_false()


def test_process_yaml_file_generic_exception(runner: YamllintRunner) -> None:
    """Test handling of generic exceptions.

    Args:
        runner: YamllintRunner instance for testing.
    """
    with (
        patch.object(runner, "get_cwd", return_value="/tmp"),
        patch.object(runner, "_get_executable_command", return_value=["yamllint"]),
        patch.object(runner, "_find_yamllint_config", return_value=None),
        patch.object(runner, "_run_subprocess", side_effect=RuntimeError("error")),
    ):
        result = runner._process_yaml_file("test.yaml", timeout=30)

        _, _, _, exec_fail, success, _ = result
        assert_that(exec_fail).is_true()
        assert_that(success).is_false()


def test_process_yaml_file_with_config(runner: YamllintRunner) -> None:
    """Test processing with config file found.

    Args:
        runner: YamllintRunner instance for testing.
    """
    with (
        patch.object(runner, "get_cwd", return_value="/tmp"),
        patch.object(runner, "_get_executable_command", return_value=["yamllint"]),
        patch.object(runner, "_find_yamllint_config", return_value="/tmp/.yamllint"),
        patch.object(runner, "_run_subprocess", return_value=(True, "")),
        patch(
            "lintro.tools.implementations.yamllint_runner.parse_yamllint_output",
            return_value=[],
        ),
    ):
        result = runner._process_yaml_file("test.yaml", timeout=30)
        assert_that(result[4]).is_true()  # success


@pytest.mark.parametrize(
    "option_name,option_value,expected_flag",
    [
        ("strict", True, "--strict"),
        ("relaxed", True, "--relaxed"),
        ("no_warnings", True, "--no-warnings"),
    ],
    ids=["strict", "relaxed", "no-warnings"],
)
def test_process_yaml_file_option_flags(
    runner: YamllintRunner,
    option_name: str,
    option_value: bool,
    expected_flag: str,
) -> None:
    """Test that option flags are passed to yamllint command.

    Args:
        runner: YamllintRunner instance for testing.
        option_name: Name of the option to set.
        option_value: Value to set for the option.
        expected_flag: Expected command line flag.
    """
    runner.options[option_name] = option_value
    captured_cmd: list[str] = []

    def capture_cmd(cmd: list[str], **kwargs: Any) -> tuple[bool, str]:
        captured_cmd.extend(cmd)
        return (True, "")

    with (
        patch.object(runner, "get_cwd", return_value="/tmp"),
        patch.object(runner, "_get_executable_command", return_value=["yamllint"]),
        patch.object(runner, "_find_yamllint_config", return_value=None),
        patch.object(runner, "_run_subprocess", side_effect=capture_cmd),
        patch(
            "lintro.tools.implementations.yamllint_runner.parse_yamllint_output",
            return_value=[],
        ),
    ):
        runner._process_yaml_file("test.yaml", timeout=30)
        assert_that(captured_cmd).contains(expected_flag)


# --- _process_yaml_file_result tests ---


def test_process_yaml_file_result_accumulates_issues(runner: YamllintRunner) -> None:
    """Test that issues are accumulated correctly.

    Args:
        runner: YamllintRunner instance for testing.
    """
    mock_issue = MagicMock()
    result = runner._process_yaml_file_result(
        issues_count=2,
        issues=[mock_issue, mock_issue],
        skipped_flag=False,
        execution_failure_flag=False,
        success_flag=True,
        file_path="test.yaml",
        all_success=True,
        all_issues=[],
        skipped_files=[],
        timeout_skipped_count=0,
        other_execution_failures=0,
        total_issues=0,
    )

    all_success, all_issues, _, _, _, total_issues = result
    assert_that(all_success).is_true()
    assert_that(len(all_issues)).is_equal_to(2)
    assert_that(total_issues).is_equal_to(2)


def test_process_yaml_file_result_tracks_skipped(runner: YamllintRunner) -> None:
    """Test that skipped files are tracked.

    Args:
        runner: YamllintRunner instance for testing.
    """
    result = runner._process_yaml_file_result(
        issues_count=0,
        issues=[],
        skipped_flag=True,
        execution_failure_flag=False,
        success_flag=False,
        file_path="timeout.yaml",
        all_success=True,
        all_issues=[],
        skipped_files=[],
        timeout_skipped_count=0,
        other_execution_failures=0,
        total_issues=0,
    )

    all_success, _, skipped_files, timeout_count, _, _ = result
    assert_that(all_success).is_false()
    assert_that(skipped_files).contains("timeout.yaml")
    assert_that(timeout_count).is_equal_to(1)


def test_process_yaml_file_result_tracks_exec_failures(runner: YamllintRunner) -> None:
    """Test that execution failures are tracked.

    Args:
        runner: YamllintRunner instance for testing.
    """
    result = runner._process_yaml_file_result(
        issues_count=0,
        issues=[],
        skipped_flag=False,
        execution_failure_flag=True,
        success_flag=False,
        file_path="error.yaml",
        all_success=True,
        all_issues=[],
        skipped_files=[],
        timeout_skipped_count=0,
        other_execution_failures=0,
        total_issues=0,
    )

    all_success, _, _, _, exec_failures, _ = result
    assert_that(all_success).is_false()
    assert_that(exec_failures).is_equal_to(1)


# --- check method tests ---


def test_check_empty_paths(runner: YamllintRunner) -> None:
    """Test check with empty paths returns success.

    Args:
        runner: YamllintRunner instance for testing.
    """
    with patch.object(runner, "_verify_tool_version", return_value=None):
        result = runner.check([])

        assert_that(result.name).is_equal_to("yamllint")
        assert_that(result.success).is_true()
        assert_that(result.output).is_equal_to("No files to check.")


def test_check_version_failure(runner: YamllintRunner) -> None:
    """Test check returns early on version check failure.

    Args:
        runner: YamllintRunner instance for testing.
    """
    version_result = ToolResult(
        name="yamllint",
        success=False,
        output="Version mismatch",
        issues_count=0,
    )
    with patch.object(runner, "_verify_tool_version", return_value=version_result):
        result = runner.check(["test.yaml"])
        assert_that(result.output).contains("Version mismatch")


# --- fix method tests ---


def test_fix_not_supported(runner: YamllintRunner) -> None:
    """Test that fix returns not supported message.

    Args:
        runner: YamllintRunner instance for testing.
    """
    result = runner.fix(["test.yaml"])

    assert_that(result.name).is_equal_to("yamllint")
    assert_that(result.success).is_false()
    assert_that(result.output).contains("cannot fix issues")
    assert_that(result.issues_count).is_equal_to(0)
