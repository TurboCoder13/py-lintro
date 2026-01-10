"""Tests for BlackPlugin.fix method."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.black import BlackPlugin


def test_fix_success_no_issues(
    black_plugin: BlackPlugin,
    mock_execution_context_for_tool: Any,
) -> None:
    """Fix returns success when no issues to fix.

    Args:
        black_plugin: The BlackPlugin instance to test.
        mock_execution_context_for_tool: Mock execution context factory.
    """
    with (
        patch.object(black_plugin, "_prepare_execution") as mock_prepare,
        patch.object(black_plugin, "_run_subprocess") as mock_run,
        patch.object(black_plugin, "_get_executable_command") as mock_exec,
        patch.object(black_plugin, "_build_common_args") as mock_args,
        patch.object(black_plugin, "_check_line_length_violations") as mock_ll,
    ):
        mock_prepare.return_value = mock_execution_context_for_tool(
            files=["test.py"],
            rel_files=["test.py"],
            cwd="/tmp",
        )

        mock_exec.return_value = ["black"]
        mock_args.return_value = []
        # All subprocess runs return success
        mock_run.return_value = (True, "All done!")
        mock_ll.return_value = []

        result = black_plugin.fix(["/tmp/test.py"], {})

        assert_that(result.success).is_true()
        assert_that(result.remaining_issues_count).is_equal_to(0)


def test_fix_success_with_fixes_applied(
    black_plugin: BlackPlugin,
    mock_execution_context_for_tool: Any,
) -> None:
    """Fix returns success when fixes applied.

    Args:
        black_plugin: The BlackPlugin instance to test.
        mock_execution_context_for_tool: Mock execution context factory.
    """
    with (
        patch.object(black_plugin, "_prepare_execution") as mock_prepare,
        patch.object(black_plugin, "_run_subprocess") as mock_run,
        patch.object(black_plugin, "_get_executable_command") as mock_exec,
        patch.object(black_plugin, "_build_common_args") as mock_args,
        patch.object(black_plugin, "_check_line_length_violations") as mock_ll,
    ):
        mock_prepare.return_value = mock_execution_context_for_tool(
            files=["test.py"],
            rel_files=["test.py"],
            cwd="/tmp",
        )

        mock_exec.return_value = ["black"]
        mock_args.return_value = []
        # First check finds issues, fix applies, final check passes
        mock_run.side_effect = [
            (False, "would reformat test.py"),  # Initial check
            (True, "reformatted test.py"),  # Fix command
            (True, "All done!"),  # Final check
        ]
        mock_ll.return_value = []

        result = black_plugin.fix(["/tmp/test.py"], {})

        assert_that(result.success).is_true()


def test_fix_timeout_during_check(
    black_plugin: BlackPlugin,
    mock_execution_context_for_tool: Any,
) -> None:
    """Fix handles timeout during initial check.

    Args:
        black_plugin: The BlackPlugin instance to test.
        mock_execution_context_for_tool: Mock execution context factory.
    """
    from lintro.models.core.tool_result import ToolResult
    from lintro.parsers.black.black_issue import BlackIssue

    # Create a properly formed timeout result
    timeout_result = ToolResult(
        name="black",
        success=False,
        output="Black execution timed out (30s limit exceeded).",
        issues_count=1,
        issues=[
            BlackIssue(
                file="execution",
                line=1,
                column=1,
                code="TIMEOUT",
                message="Black execution timed out",
                fixable=False,
            ),
        ],
        initial_issues_count=1,
        fixed_issues_count=0,
        remaining_issues_count=1,
    )

    with (
        patch.object(black_plugin, "_prepare_execution") as mock_prepare,
        patch.object(black_plugin, "_run_subprocess") as mock_run,
        patch.object(black_plugin, "_get_executable_command") as mock_exec,
        patch.object(black_plugin, "_build_common_args") as mock_args,
        patch.object(
            black_plugin,
            "_handle_timeout_error",
            return_value=timeout_result,
        ),
    ):
        mock_prepare.return_value = mock_execution_context_for_tool(
            files=["test.py"],
            rel_files=["test.py"],
            cwd="/tmp",
        )

        mock_exec.return_value = ["black"]
        mock_args.return_value = []
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="black", timeout=30)

        result = black_plugin.fix(["/tmp/test.py"], {})

        assert_that(result.success).is_false()
        assert_that(result.output).contains("timed out")


def test_fix_early_return_when_should_skip(
    black_plugin: BlackPlugin,
    mock_execution_context_for_tool: Any,
) -> None:
    """Fix returns early result when should_skip is True.

    Args:
        black_plugin: The BlackPlugin instance to test.
        mock_execution_context_for_tool: Mock execution context factory.
    """
    with patch.object(black_plugin, "_prepare_execution") as mock_prepare:
        ctx = mock_execution_context_for_tool(should_skip=True)
        ctx.early_result = MagicMock(success=True, issues_count=0)
        mock_prepare.return_value = ctx

        result = black_plugin.fix(["/tmp"], {})

        assert_that(result.success).is_true()


def test_fix_with_diff_option(
    black_plugin: BlackPlugin,
    mock_execution_context_for_tool: Any,
) -> None:
    """Fix uses --diff flag when diff option is set.

    Args:
        black_plugin: The BlackPlugin instance to test.
        mock_execution_context_for_tool: Mock execution context factory.
    """
    with (
        patch.object(black_plugin, "_prepare_execution") as mock_prepare,
        patch.object(black_plugin, "_run_subprocess") as mock_run,
        patch.object(black_plugin, "_get_executable_command") as mock_exec,
        patch.object(black_plugin, "_build_common_args") as mock_args,
        patch.object(black_plugin, "_check_line_length_violations") as mock_ll,
    ):
        mock_prepare.return_value = mock_execution_context_for_tool(
            files=["test.py"],
            rel_files=["test.py"],
            cwd="/tmp",
        )

        mock_exec.return_value = ["black"]
        mock_args.return_value = []
        mock_run.return_value = (True, "--- test.py\n+++ test.py")
        mock_ll.return_value = []

        black_plugin.set_options(diff=True)
        result = black_plugin.fix(["/tmp/test.py"], {})

        # With diff=True, it skips initial check
        assert_that(result.initial_issues_count).is_equal_to(0)
