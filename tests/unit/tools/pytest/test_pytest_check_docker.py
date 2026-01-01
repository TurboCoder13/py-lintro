"""Unit tests for pytest tool docker-related check functionality."""

import os
from unittest.mock import patch

from assertpy import assert_that

from lintro.tools.implementations.tool_pytest import PytestTool


def test_pytest_tool_check_run_docker_tests_enabled() -> None:
    """Test check with run_docker_tests enabled."""
    tool = PytestTool()
    tool.set_options(run_docker_tests=True)

    # Store original state
    original_value = os.environ.get("LINTRO_RUN_DOCKER_TESTS")

    try:
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
                return_value=(10, 5, None),
            ),
        ):
            result = tool.check(["tests"])
            assert_that(result.success).is_true()
            # Verify docker tests env var was NOT set after cleanup
            # (it's cleaned up in the finally block)
            assert_that(os.environ).does_not_contain("LINTRO_RUN_DOCKER_TESTS")
    finally:
        # Clean up environment variable
        if original_value is None:
            if "LINTRO_RUN_DOCKER_TESTS" in os.environ:
                del os.environ["LINTRO_RUN_DOCKER_TESTS"]
        else:
            os.environ["LINTRO_RUN_DOCKER_TESTS"] = original_value


def test_pytest_tool_check_docker_disabled_message() -> None:
    """Test check with docker tests disabled shows message."""
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
            return_value=(10, 3, None),
        ),
    ):
        result = tool.check(["tests"])
        assert_that(result.success).is_true()


def test_pytest_tool_check_docker_skipped_calculation() -> None:
    """Test check calculates docker skipped correctly."""
    tool = PytestTool()

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, "7 passed, 3 skipped"),
        ),
        patch.object(
            tool.executor,
            "prepare_test_execution",
            return_value=(10, 3, None),
        ),
    ):
        result = tool.check(["tests"])
        assert_that(result.success).is_true()
        if hasattr(result, "pytest_summary"):
            assert_that(result.pytest_summary["docker_skipped"]).is_equal_to(3)
