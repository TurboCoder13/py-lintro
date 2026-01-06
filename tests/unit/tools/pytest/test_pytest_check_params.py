"""Unit tests for pytest tool check method parameter handling."""

from unittest.mock import Mock, patch

from assertpy import assert_that

from lintro.models.core.tool_result import ToolResult
from lintro.tools.implementations.tool_pytest import PytestTool


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
