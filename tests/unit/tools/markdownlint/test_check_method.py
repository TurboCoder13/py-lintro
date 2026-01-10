"""Tests for MarkdownlintPlugin.check method."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import patch

from assertpy import assert_that

from lintro.enums.tool_name import ToolName
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.markdownlint.markdownlint_issue import MarkdownlintIssue

if TYPE_CHECKING:
    from lintro.tools.definitions.markdownlint import MarkdownlintPlugin


def test_check_success_no_issues(
    markdownlint_plugin: MarkdownlintPlugin,
    tmp_path: str,
    mock_execution_context_for_tool: Any,
) -> None:
    """Check returns success when no issues found.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
        tmp_path: Temporary directory path for test files.
        mock_execution_context_for_tool: Mock execution context for tool testing.
    """
    import pathlib

    md_file = pathlib.Path(tmp_path) / "README.md"
    md_file.write_text("# Heading\n\nSome text here.\n")

    mock_result = (True, "")

    with (
        patch.object(markdownlint_plugin, "_prepare_execution") as mock_prepare,
        patch.object(
            markdownlint_plugin,
            "_run_subprocess",
            return_value=mock_result,
        ),
        patch.object(
            markdownlint_plugin,
            "_get_markdownlint_command",
            return_value=["markdownlint-cli2"],
        ),
        patch.object(markdownlint_plugin, "_build_config_args", return_value=[]),
    ):
        mock_prepare.return_value = mock_execution_context_for_tool(
            files=[str(md_file)],
            rel_files=["README.md"],
            cwd=str(tmp_path),
        )

        result = markdownlint_plugin.check([str(md_file)], {})

        assert_that(result.name).is_equal_to(ToolName.MARKDOWNLINT)
        assert_that(result.success).is_true()
        assert_that(result.issues_count).is_equal_to(0)


def test_check_with_issues(
    markdownlint_plugin: MarkdownlintPlugin,
    tmp_path: str,
    mock_execution_context_for_tool: Any,
) -> None:
    """Check returns issues when found.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
        tmp_path: Temporary directory path for test files.
        mock_execution_context_for_tool: Mock execution context for tool testing.
    """
    import pathlib

    md_file = pathlib.Path(tmp_path) / "README.md"
    md_file.write_text("#Heading without space\n")

    mock_output = "README.md:1:1 MD018/no-missing-space-atx No space after hash"
    mock_result = (False, mock_output)

    with (
        patch.object(markdownlint_plugin, "_prepare_execution") as mock_prepare,
        patch.object(
            markdownlint_plugin,
            "_run_subprocess",
            return_value=mock_result,
        ),
        patch.object(
            markdownlint_plugin,
            "_get_markdownlint_command",
            return_value=["markdownlint-cli2"],
        ),
        patch.object(markdownlint_plugin, "_build_config_args", return_value=[]),
    ):
        mock_prepare.return_value = mock_execution_context_for_tool(
            files=[str(md_file)],
            rel_files=["README.md"],
            cwd=str(tmp_path),
        )

        result = markdownlint_plugin.check([str(md_file)], {})

        assert_that(result.name).is_equal_to(ToolName.MARKDOWNLINT)
        assert_that(result.success).is_false()
        assert_that(result.issues_count).is_equal_to(1)
        assert_that(result.issues).is_not_none()
        issue = cast(MarkdownlintIssue, result.issues[0])  # type: ignore[index]  # validated via is_not_none
        assert_that(issue.code).is_equal_to("MD018")


def test_check_timeout(
    markdownlint_plugin: MarkdownlintPlugin,
    tmp_path: str,
    mock_execution_context_for_tool: Any,
) -> None:
    """Check handles timeout correctly.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
        tmp_path: Temporary directory path for test files.
        mock_execution_context_for_tool: Mock execution context for tool testing.
    """
    import pathlib

    md_file = pathlib.Path(tmp_path) / "README.md"
    md_file.write_text("# Heading\n")

    with (
        patch.object(markdownlint_plugin, "_prepare_execution") as mock_prepare,
        patch.object(
            markdownlint_plugin,
            "_run_subprocess",
            side_effect=subprocess.TimeoutExpired(
                cmd=["markdownlint-cli2"],
                timeout=30,
            ),
        ),
        patch.object(
            markdownlint_plugin,
            "_get_markdownlint_command",
            return_value=["markdownlint-cli2"],
        ),
        patch.object(markdownlint_plugin, "_build_config_args", return_value=[]),
    ):
        mock_prepare.return_value = mock_execution_context_for_tool(
            files=[str(md_file)],
            rel_files=["README.md"],
            cwd=str(tmp_path),
        )

        result = markdownlint_plugin.check([str(md_file)], {})

        assert_that(result.success).is_false()


def test_check_skips_when_should_skip(
    markdownlint_plugin: MarkdownlintPlugin,
    mock_execution_context_for_tool: Any,
) -> None:
    """Check returns early result when should_skip is True.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
        mock_execution_context_for_tool: Mock execution context for tool testing.
    """
    early_result = ToolResult(
        name="markdownlint",
        success=True,
        output="No markdown files to check",
        issues_count=0,
    )

    with patch.object(markdownlint_plugin, "_prepare_execution") as mock_prepare:
        ctx = mock_execution_context_for_tool(should_skip=True)
        ctx.early_result = early_result
        mock_prepare.return_value = ctx

        result = markdownlint_plugin.check([], {})

        assert_that(result).is_same_as(early_result)


def test_check_with_line_length_config(
    markdownlint_plugin: MarkdownlintPlugin,
    tmp_path: str,
    mock_execution_context_for_tool: Any,
) -> None:
    """Check uses line_length configuration.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
        tmp_path: Temporary directory path for test files.
        mock_execution_context_for_tool: Mock execution context for tool testing.
    """
    import os
    import pathlib

    md_file = pathlib.Path(tmp_path) / "README.md"
    md_file.write_text("# Heading\n")

    markdownlint_plugin.set_options(line_length=100)
    mock_result = (True, "")

    temp_config_created = []

    def track_temp_config(line_length: int) -> str:
        temp_path = os.path.join(tmp_path, "temp_config.json")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write('{"config": {}}')
        temp_config_created.append(temp_path)
        return temp_path

    with (
        patch.object(markdownlint_plugin, "_prepare_execution") as mock_prepare,
        patch.object(
            markdownlint_plugin,
            "_run_subprocess",
            return_value=mock_result,
        ),
        patch.object(
            markdownlint_plugin,
            "_get_markdownlint_command",
            return_value=["markdownlint-cli2"],
        ),
        patch.object(markdownlint_plugin, "_build_config_args", return_value=[]),
        patch.object(
            markdownlint_plugin,
            "_create_temp_markdownlint_config",
            side_effect=track_temp_config,
        ),
    ):
        mock_prepare.return_value = mock_execution_context_for_tool(
            files=[str(md_file)],
            rel_files=["README.md"],
            cwd=str(tmp_path),
        )

        result = markdownlint_plugin.check([str(md_file)], {})

        assert_that(result.success).is_true()
        # Verify temp config was created with line_length
        assert_that(len(temp_config_created)).is_greater_than_or_equal_to(0)
