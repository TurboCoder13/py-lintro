"""Unit tests for basic pytest tool check method functionality."""

from unittest.mock import Mock, patch

import pytest
from assertpy import assert_that

from lintro.models.core.tool_result import ToolResult
from lintro.parsers.pytest.pytest_issue import PytestIssue
from lintro.tools.implementations.tool_pytest import PytestTool


def test_pytest_tool_check_no_files() -> None:
    """Test check method with no files."""
    tool = PytestTool()

    # Mock subprocess to simulate no tests found
    with (
        patch.object(tool, "_verify_tool_version", return_value=None),
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, "no tests ran"),
        ),
        patch.object(tool, "_parse_output", return_value=[]),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(0, 0, None),
        ),
        patch.object(
            tool.executor,
            "execute_tests",
            return_value=(True, "no tests ran", 0),
        ),
        patch.object(
            tool.result_processor,
            "process_test_results",
            return_value=(
                {
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "error": 0,
                    "total": 0,
                    "duration": 0.0,
                },
                [],
            ),
        ),
        patch.object(
            tool.result_processor,
            "build_result",
            return_value=ToolResult(
                name="pytest",
                success=True,
                issues=[],
                output=(
                    '{"passed": 0, "failed": 0, "skipped": 0, '
                    '"error": 0, "total": 0, "duration": 0.0}'
                ),
                issues_count=0,
            ),
        ),
    ):
        result = tool.check()

        assert_that(result.name).is_equal_to("pytest")
        assert_that(result.success).is_true()
        assert_that(result.issues).is_empty()


def test_pytest_tool_check_success() -> None:
    """Test successful check method."""
    tool = PytestTool()

    mock_result = Mock()
    mock_result.return_code = 0
    mock_result.stdout = "All tests passed"
    mock_result.stderr = ""

    with (
        patch.object(tool, "_verify_tool_version", return_value=None),
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(511, 0, None),
        ),
        patch.object(
            tool.executor,
            "execute_tests",
            return_value=(True, "All tests passed\n511 passed in 18.53s", 0),
        ),
        patch.object(tool, "_parse_output", return_value=[]),
        patch.object(
            tool.result_processor,
            "process_test_results",
            return_value=(
                {
                    "passed": 511,
                    "failed": 0,
                    "skipped": 0,
                    "error": 0,
                    "total": 511,
                    "duration": 18.53,
                },
                [],
            ),
        ),
        patch.object(
            tool.result_processor,
            "build_result",
            return_value=ToolResult(
                name="pytest",
                success=True,
                issues=[],
                output=(
                    '{"passed": 511, "failed": 0, "skipped": 0, '
                    '"error": 0, "total": 511, "duration": 18.53}'
                ),
                issues_count=0,
            ),
        ),
    ):
        result = tool.check(["test_file.py"])

        assert_that(result.name).is_equal_to("pytest")
        assert_that(result.success).is_true()
        assert_that(result.issues).is_empty()
        # Output should contain JSON summary
        assert_that(result.output).contains('"passed": 511')
        assert_that(result.output).contains('"failed": 0')
        assert_that(result.issues_count).is_equal_to(0)


def test_pytest_tool_check_failure() -> None:
    """Test failed check method."""
    tool = PytestTool()

    mock_issue = PytestIssue(
        file="test_file.py",
        line=0,
        test_name="test_failure",
        message="AssertionError",
        test_status="FAILED",
    )

    with (
        patch.object(tool, "_verify_tool_version", return_value=None),
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(511, 0, None),
        ),
        patch.object(
            tool.executor,
            "execute_tests",
            return_value=(
                False,
                "FAILED test_file.py::test_failure - AssertionError\n"
                "510 passed, 1 failed in 18.53s",
                1,
            ),
        ),
        patch.object(tool, "_parse_output", return_value=[mock_issue]),
        patch.object(
            tool.result_processor,
            "process_test_results",
            return_value=(
                {
                    "passed": 510,
                    "failed": 1,
                    "skipped": 0,
                    "error": 0,
                    "total": 511,
                    "duration": 18.53,
                },
                [mock_issue],
            ),
        ),
    ):
        result = tool.check(["test_file.py"])

        assert_that(result.name).is_equal_to("pytest")
        assert_that(result.success).is_false()
        assert_that(result.issues).is_length(1)
        # Type narrowing for mypy
        assert_that(result.issues).is_not_none()
        issues = result.issues
        if issues is None:
            pytest.fail("issues should not be None")
        first_issue = issues[0]
        assert_that(isinstance(first_issue, PytestIssue)).is_true()
        if not isinstance(first_issue, PytestIssue):
            pytest.fail("first_issue should be PytestIssue")
        assert_that(first_issue.file).is_equal_to("test_file.py")
        assert_that(first_issue.test_name).is_equal_to("test_failure")
        assert_that(first_issue.test_status).is_equal_to("FAILED")
        assert_that(first_issue.message).contains("AssertionError")
        # Output should contain JSON summary
        assert_that(result.output).contains('"failed": 1')
        assert_that(result.issues_count).is_equal_to(1)


def test_pytest_tool_check_exception() -> None:
    """Test check method with exception."""
    tool = PytestTool()

    with (
        patch.object(tool, "_verify_tool_version", return_value=None),
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(511, 0, None),
        ),
        patch.object(
            tool.executor,
            "execute_tests",
            side_effect=Exception("Test error"),
        ),
    ):
        result = tool.check(["test_file.py"])

        assert_that(result.name).is_equal_to("pytest")
        assert_that(result.success).is_false()
        assert_that(result.issues).is_empty()
        assert_that(result.output).contains("Test error")


def test_pytest_tool_fix_default_behavior() -> None:
    """Test that fix raises NotImplementedError when can_fix is False (default)."""
    tool = PytestTool()
    assert_that(tool.can_fix).is_false()

    with pytest.raises(NotImplementedError):
        tool.fix(["test_file.py"])


def test_pytest_tool_fix_with_can_fix_true() -> None:
    """Test that fix raises NotImplementedError even when can_fix is True."""
    tool = PytestTool()
    # Mock can_fix to True to test the second check
    tool.can_fix = True

    with pytest.raises(
        NotImplementedError,
        match="pytest does not support fixing issues",
    ):
        tool.fix(["test_file.py"])


def test_pytest_tool_check_paths_vs_files_precedence() -> None:
    """Test that paths parameter takes precedence over files."""
    tool = PytestTool()

    # Create a mock to capture the command passed to execute_tests
    mock_execute_tests = Mock(return_value=(True, "All tests passed", 0))

    with (
        patch.object(tool, "_verify_tool_version", return_value=None),
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(0, 0, None),
        ),
        patch.object(
            tool.executor,
            "execute_tests",
            mock_execute_tests,
        ),
        patch.object(tool, "_parse_output", return_value=[]),
        patch.object(
            tool.result_processor,
            "process_test_results",
            return_value=(
                {
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "error": 0,
                    "total": 0,
                    "duration": 0.0,
                },
                [],
            ),
        ),
        patch.object(
            tool.result_processor,
            "build_result",
            return_value=ToolResult(
                name="pytest",
                success=True,
                issues=[],
                output='{"passed": 0}',
                issues_count=0,
            ),
        ),
    ):
        # Both paths and files provided; paths should be used
        tool.check(files=["file.py"], paths=["path/"])

        # Verify execute_tests was called
        assert_that(mock_execute_tests.called).is_true()
        # Get the command that was passed to execute_tests
        call_args = mock_execute_tests.call_args
        cmd = call_args[0][0]  # First positional argument is the command list

        # Assert that paths argument ("path/") is in the command
        assert_that(cmd).contains("path/").described_as(
            f"Expected 'path/' in command, got: {cmd}",
        )
        # Assert that files argument ("file.py") is NOT in the command
        # since paths takes precedence over files
        assert_that(cmd).does_not_contain("file.py").described_as(
            f"Expected 'file.py' NOT in command (paths takes precedence), got: {cmd}",
        )


def test_pytest_tool_check_discovers_test_files() -> None:
    """Verify that check discovers test files without files or paths."""
    tool = PytestTool()

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, "5 passed in 0.10s"),
        ),
        patch.object(tool, "_parse_output", return_value=[]),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(5, 0, None),
        ),
    ):
        result = tool.check()

        assert_that(result.name).is_equal_to("pytest")
        assert_that(result.success).is_true()


def test_pytest_tool_check_target_files_none() -> None:
    """Test check with target_files as None."""
    tool = PytestTool()

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, "All tests passed"),
        ),
        patch.object(tool, "_parse_output", return_value=[]),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(10, 0, None),
        ),
    ):
        result = tool.check(files=None, paths=None)
        assert_that(result.success).is_true()


def test_pytest_tool_check_target_files_dot() -> None:
    """Test check with target_files as just '.'."""
    tool = PytestTool()

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, "All tests passed"),
        ),
        patch.object(tool, "_parse_output", return_value=[]),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(10, 0, None),
        ),
    ):
        result = tool.check(files=["."])
        assert_that(result.success).is_true()
