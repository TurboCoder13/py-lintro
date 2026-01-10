"""Tests for BlackPlugin.check method."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.black import BlackPlugin


def test_check_includes_line_length_violations(
    black_plugin: BlackPlugin,
    mock_execution_context_for_tool: Any,
) -> None:
    """Check includes line length violations in results.

    Args:
        black_plugin: The BlackPlugin instance to test.
        mock_execution_context_for_tool: Mock execution context factory.
    """
    from lintro.parsers.black.black_issue import BlackIssue

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
        mock_run.return_value = (True, "All done!")
        mock_ll.return_value = [
            BlackIssue(
                file="test.py",
                line=10,
                column=89,
                code="E501",
                message="Line too long",
                severity="error",
                fixable=False,
            ),
        ]

        result = black_plugin.check(["/tmp/test.py"], {})

        assert_that(result.success).is_false()
        assert_that(result.issues_count).is_equal_to(1)
