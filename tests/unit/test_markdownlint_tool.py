"""Unit tests for MarkdownlintTool."""

from unittest.mock import MagicMock, patch

import pytest

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
    assert markdownlint_tool.name == "markdownlint"
    assert markdownlint_tool.can_fix is False
    assert "*.md" in markdownlint_tool.config.file_patterns
    assert "*.markdown" in markdownlint_tool.config.file_patterns


def test_markdownlint_uses_npx_command(markdownlint_tool: MarkdownlintTool) -> None:
    """Verify markdownlint uses npx markdownlint-cli2 command.

    Args:
        markdownlint_tool: MarkdownlintTool instance for testing.
    """
    cmd = markdownlint_tool._get_markdownlint_command()
    assert "npx" in cmd
    assert "markdownlint-cli2" in cmd


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
    assert cmd == ["markdownlint-cli2"]


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
        assert result.success is True
        assert result.issues_count == 0
        assert "No files to check" in result.output


def test_markdownlint_check_with_issues(
    markdownlint_tool: MarkdownlintTool,
    tmp_path: pytest.TempPathFactory,
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
        assert result.success is False
        assert result.issues_count == 1
        assert len(result.issues) == 1
        assert isinstance(result.issues[0], MarkdownlintIssue)


def test_markdownlint_fix_not_supported(markdownlint_tool: MarkdownlintTool) -> None:
    """Return error message when fix is called.

    Args:
        markdownlint_tool: MarkdownlintTool instance for testing.
    """
    result = markdownlint_tool.fix(paths=["test.md"])
    assert result.success is False
    assert "cannot fix" in result.output.lower()
    assert result.issues_count == 0
