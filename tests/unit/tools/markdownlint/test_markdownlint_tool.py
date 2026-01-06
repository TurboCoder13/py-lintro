"""Unit tests for MarkdownlintTool."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from lintro.parsers.markdownlint.markdownlint_issue import MarkdownlintIssue
from lintro.tools.implementations.tool_markdownlint import MarkdownlintTool


@pytest.fixture()
def markdownlint_tool() -> MarkdownlintTool:
    """Provide a MarkdownlintTool instance for testing.

    Returns:
        MarkdownlintTool: Configured MarkdownlintTool instance.
    """
    return MarkdownlintTool()


def test_markdownlint_tool_initialization(markdownlint_tool: MarkdownlintTool) -> None:
    """Verify MarkdownlintTool initializes with correct defaults.

    Args:
        markdownlint_tool: MarkdownlintTool instance for testing.
    """
    assert_that(markdownlint_tool.name).is_equal_to("markdownlint")
    assert_that(markdownlint_tool.can_fix).is_false()
    assert_that(markdownlint_tool.config.file_patterns).contains("*.md")
    assert_that(markdownlint_tool.config.file_patterns).contains("*.markdown")


@patch("shutil.which")
def test_markdownlint_uses_npx_command(
    mock_which: MagicMock,
    markdownlint_tool: MarkdownlintTool,
) -> None:
    """Verify markdownlint uses npx markdownlint-cli2 command.

    Args:
        mock_which: Mock for shutil.which to simulate npx being available.
        markdownlint_tool: MarkdownlintTool instance for testing.
    """
    mock_which.return_value = "/usr/bin/npx"
    cmd = markdownlint_tool._get_markdownlint_command()
    assert_that(cmd).contains("npx")
    assert_that(cmd).contains("markdownlint-cli2")


@patch("shutil.which")
def test_markdownlint_falls_back_when_no_npx(
    mock_which: MagicMock,
    markdownlint_tool: MarkdownlintTool,
) -> None:
    """Fall back to direct executable when npx is not available.

    Args:
        mock_which: Mock for shutil.which.
        markdownlint_tool: MarkdownlintTool instance for testing.
    """
    mock_which.return_value = None
    cmd = markdownlint_tool._get_markdownlint_command()
    assert_that(cmd).is_equal_to(["markdownlint-cli2"])


def test_markdownlint_check_no_files(markdownlint_tool: MarkdownlintTool) -> None:
    """Return success when no files are found.

    Args:
        markdownlint_tool: MarkdownlintTool instance for testing.
    """
    with patch.object(
        markdownlint_tool,
        "_verify_tool_version",
        return_value=None,
    ):
        result = markdownlint_tool.check(paths=[])
        assert_that(result.success).is_true()
        assert_that(result.issues_count).is_equal_to(0)
        assert_that(result.output).contains("No files to check")


def test_markdownlint_check_with_issues(
    markdownlint_tool: MarkdownlintTool,
    tmp_path: Path,
) -> None:
    """Parse markdownlint output and return issues.

    Args:
        markdownlint_tool: MarkdownlintTool instance for testing.
        tmp_path: Pytest fixture for temporary directories.
    """
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test\n\nSome content")

    with (
        patch.object(
            markdownlint_tool,
            "_verify_tool_version",
            return_value=None,
        ),
        patch.object(
            markdownlint_tool,
            "_run_subprocess",
            return_value=(
                False,
                "test.md:1:1 MD041/first-line-heading First line should be a heading",
            ),
        ),
    ):
        result = markdownlint_tool.check(paths=[str(test_file)])
        assert_that(result.success).is_false()
        assert_that(result.issues_count).is_equal_to(1)
        assert_that(result.issues).is_not_none()
        assert_that(result.issues).is_length(1)
        if result.issues is not None:
            assert_that(result.issues[0]).is_instance_of(MarkdownlintIssue)


def test_markdownlint_fix_not_supported(markdownlint_tool: MarkdownlintTool) -> None:
    """Raise NotImplementedError when fix is called.

    Args:
        markdownlint_tool: MarkdownlintTool instance for testing.
    """
    with pytest.raises(NotImplementedError, match="cannot fix"):
        markdownlint_tool.fix(paths=["test.md"])
