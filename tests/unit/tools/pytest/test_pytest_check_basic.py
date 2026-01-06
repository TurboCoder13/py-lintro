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


@pytest.mark.parametrize(
    "set_can_fix,expected_match",
    [
        (False, None),
        (True, "pytest does not support fixing issues"),
    ],
    ids=["can_fix_false", "can_fix_true"],
)
def test_pytest_tool_fix_raises_not_implemented(
    set_can_fix: bool,
    expected_match: str | None,
) -> None:
    """Test that fix raises NotImplementedError regardless of can_fix value.

    Args:
        set_can_fix: Whether to set can_fix to True.
        expected_match: Expected match string for the exception.
    """
    tool = PytestTool()
    if set_can_fix:
        tool.can_fix = True
    else:
        assert_that(tool.can_fix).is_false()

    with pytest.raises(NotImplementedError, match=expected_match):
        tool.fix(["test_file.py"])


@pytest.mark.parametrize(
    "files,paths,description",
    [
        (None, None, "discovers test files without files or paths"),
        (None, None, "target_files as None"),
        (["."], None, "target_files as just '.'"),
    ],
    ids=["discover-files", "files-none", "files-dot"],
)
def test_pytest_tool_check_target_variants(
    files: list[str] | None,
    paths: list[str] | None,
    description: str,
) -> None:
    """Test check with various file/path combinations.

    Args:
        files: List of files to check.
        paths: List of paths to check.
        description: Description of the test case.
    """
    from tests.unit.tools.pytest.conftest import patch_pytest_tool_for_check

    tool = PytestTool()
    with patch_pytest_tool_for_check(tool):
        result = tool.check(files=files, paths=paths)
        assert_that(result.name).is_equal_to("pytest")
        assert_that(result.success).is_true()
