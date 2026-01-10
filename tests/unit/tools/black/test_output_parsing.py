"""Tests for Black output parsing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.black import BlackPlugin


def test_check_parses_black_output_correctly(
    black_plugin: BlackPlugin,
    mock_execution_context_for_tool: Any,
) -> None:
    """Check correctly parses Black output with issues.

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
            files=["file1.py", "file2.py"],
            rel_files=["file1.py", "file2.py"],
            cwd="/tmp",
        )

        mock_exec.return_value = ["black"]
        mock_args.return_value = []
        # Black output with multiple files having issues
        mock_run.return_value = (
            False,
            "would reformat file1.py\nwould reformat file2.py\n"
            "Oh no! 2 files would be reformatted.",
        )
        mock_ll.return_value = []

        result = black_plugin.check(["/tmp"], {})

        assert_that(result.success).is_false()
        assert_that(result.issues_count).is_equal_to(2)
        assert_that(result.issues).is_not_none()
        assert_that(result.issues[0].file).is_equal_to("file1.py")  # type: ignore[index]  # validated via is_not_none
        assert_that(result.issues[1].file).is_equal_to("file2.py")  # type: ignore[index]  # validated via is_not_none
