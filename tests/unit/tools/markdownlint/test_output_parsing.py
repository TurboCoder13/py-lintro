"""Tests for markdownlint output parsing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from unittest.mock import patch

from assertpy import assert_that

from lintro.parsers.markdownlint.markdownlint_issue import MarkdownlintIssue

if TYPE_CHECKING:
    from lintro.tools.definitions.markdownlint import MarkdownlintPlugin


def test_parse_single_issue(
    markdownlint_plugin: MarkdownlintPlugin,
    tmp_path: str,
    mock_execution_context_for_tool: Any,
) -> None:
    """Parse single issue from markdownlint output.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
        tmp_path: Temporary directory path for test files.
        mock_execution_context_for_tool: Mock execution context for tool testing.
    """
    import pathlib

    md_file = pathlib.Path(tmp_path) / "test.md"
    md_file.write_text("#Bad heading\n")

    mock_output = "test.md:1:1 MD018/no-missing-space-atx No space after hash"
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
            rel_files=["test.md"],
            cwd=str(tmp_path),
        )

        result = markdownlint_plugin.check([str(md_file)], {})

        assert_that(result.issues_count).is_equal_to(1)
        assert_that(result.issues).is_not_none()
        issue = cast(MarkdownlintIssue, result.issues[0])  # type: ignore[index]  # validated via is_not_none
        assert_that(issue.file).is_equal_to("test.md")
        assert_that(issue.line).is_equal_to(1)
        assert_that(issue.column).is_equal_to(1)
        assert_that(issue.code).is_equal_to("MD018")


def test_parse_multiple_issues(
    markdownlint_plugin: MarkdownlintPlugin,
    tmp_path: str,
    mock_execution_context_for_tool: Any,
) -> None:
    """Parse multiple issues from markdownlint output.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
        tmp_path: Temporary directory path for test files.
        mock_execution_context_for_tool: Mock execution context for tool testing.
    """
    import pathlib

    md_file = pathlib.Path(tmp_path) / "test.md"
    md_file.write_text("#Bad heading\nNo blank line\n")

    mock_output = (
        "test.md:1:1 MD018/no-missing-space-atx No space after hash\n"
        "test.md:2 MD022/blanks-around-headings Headings should be surrounded"
    )
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
            rel_files=["test.md"],
            cwd=str(tmp_path),
        )

        result = markdownlint_plugin.check([str(md_file)], {})

        assert_that(result.issues_count).is_equal_to(2)
        assert_that(result.issues).is_not_none()
        first_issue = cast(MarkdownlintIssue, result.issues[0])  # type: ignore[index]  # validated via is_not_none
        second_issue = cast(MarkdownlintIssue, result.issues[1])  # type: ignore[index]  # validated via is_not_none
        assert_that(first_issue.code).is_equal_to("MD018")
        assert_that(second_issue.code).is_equal_to("MD022")


def test_parse_issue_without_column(
    markdownlint_plugin: MarkdownlintPlugin,
    tmp_path: str,
    mock_execution_context_for_tool: Any,
) -> None:
    """Parse issue without column number.

    Args:
        markdownlint_plugin: The MarkdownlintPlugin instance to test.
        tmp_path: Temporary directory path for test files.
        mock_execution_context_for_tool: Mock execution context for tool testing.
    """
    import pathlib

    md_file = pathlib.Path(tmp_path) / "test.md"
    md_file.write_text("# Heading\nList\n")

    mock_output = (
        "test.md:2 MD032/blanks-around-lists Lists should be surrounded by blank lines"
    )
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
            rel_files=["test.md"],
            cwd=str(tmp_path),
        )

        result = markdownlint_plugin.check([str(md_file)], {})

        assert_that(result.issues_count).is_equal_to(1)
        assert_that(result.issues).is_not_none()
        issue = result.issues[0]  # type: ignore[index]  # validated via is_not_none
        assert_that(issue.line).is_equal_to(2)
        assert_that(issue.column).is_equal_to(0)  # Default when not provided
