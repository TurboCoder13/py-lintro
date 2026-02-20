"""Unit tests for GitHubStyle formatter.

Tests verify GitHubStyle emits correct GitHub Actions annotation commands
with proper severity mapping, escaping, and edge-case handling.
"""

from __future__ import annotations

from assertpy import assert_that

from lintro.formatters.styles.github import GitHubStyle


def test_github_style_single_error_annotation(github_style: GitHubStyle) -> None:
    """GitHubStyle emits an ::error annotation for error severity.

    Args:
        github_style: The GitHubStyle formatter instance.
    """
    columns = ["File", "Line", "Column", "Code", "Message", "Severity"]
    rows = [["src/main.py", "10", "5", "E501", "Line too long", "error"]]

    result = github_style.format(columns, rows, tool_name="ruff")

    assert_that(result).starts_with("::error ")
    assert_that(result).contains("file=src/main.py")
    assert_that(result).contains("line=10")
    assert_that(result).contains("col=5")
    assert_that(result).contains("title=ruff(E501)")
    assert_that(result).contains("::Line too long")


def test_github_style_warning_severity(github_style: GitHubStyle) -> None:
    """GitHubStyle maps warning severity to ::warning.

    Args:
        github_style: The GitHubStyle formatter instance.
    """
    columns = ["File", "Line", "Column", "Code", "Message", "Severity"]
    rows = [["a.py", "1", "-", "W001", "Unused import", "warning"]]

    result = github_style.format(columns, rows, tool_name="tool")

    assert_that(result).starts_with("::warning ")


def test_github_style_info_severity_maps_to_notice(github_style: GitHubStyle) -> None:
    """GitHubStyle maps info severity to ::notice.

    Args:
        github_style: The GitHubStyle formatter instance.
    """
    columns = ["File", "Line", "Column", "Code", "Message", "Severity"]
    rows = [["a.py", "1", "-", "I001", "Info msg", "info"]]

    result = github_style.format(columns, rows, tool_name="tool")

    assert_that(result).starts_with("::notice ")


def test_github_style_alias_severity(github_style: GitHubStyle) -> None:
    """GitHubStyle normalizes alias severities (e.g. HIGH → error).

    Args:
        github_style: The GitHubStyle formatter instance.
    """
    columns = ["File", "Line", "Column", "Code", "Message", "Severity"]
    rows = [["a.py", "1", "-", "B001", "Hardcoded password", "HIGH"]]

    result = github_style.format(columns, rows, tool_name="bandit")

    assert_that(result).starts_with("::error ")


def test_github_style_missing_severity_defaults_to_warning(
    github_style: GitHubStyle,
) -> None:
    """GitHubStyle defaults to ::warning when severity column is empty.

    Args:
        github_style: The GitHubStyle formatter instance.
    """
    columns = ["File", "Line", "Column", "Code", "Message", "Severity"]
    rows = [["a.py", "1", "-", "X", "Some issue", ""]]

    result = github_style.format(columns, rows, tool_name="tool")

    assert_that(result).starts_with("::warning ")


def test_github_style_escapes_special_characters(github_style: GitHubStyle) -> None:
    """GitHubStyle escapes %, CR, and LF in messages.

    Args:
        github_style: The GitHubStyle formatter instance.
    """
    columns = ["File", "Line", "Column", "Code", "Message", "Severity"]
    rows = [["a.py", "1", "-", "X", "100% done\r\nNext", "error"]]

    result = github_style.format(columns, rows, tool_name="tool")

    assert_that(result).contains("100%25 done%0D%0ANext")
    assert_that(result).does_not_contain("\r")
    assert_that(result).does_not_contain("\n")


def test_github_style_empty_rows_returns_empty_string(
    github_style: GitHubStyle,
) -> None:
    """GitHubStyle returns empty string for no rows.

    Args:
        github_style: The GitHubStyle formatter instance.
    """
    result = github_style.format(["File", "Message"], [], tool_name="tool")

    assert_that(result).is_equal_to("")


def test_github_style_multiple_rows(github_style: GitHubStyle) -> None:
    """GitHubStyle emits one annotation per row.

    Args:
        github_style: The GitHubStyle formatter instance.
    """
    columns = ["File", "Line", "Column", "Code", "Message", "Severity"]
    rows = [
        ["a.py", "1", "-", "E1", "First", "error"],
        ["b.py", "2", "3", "W1", "Second", "warning"],
    ]

    result = github_style.format(columns, rows, tool_name="tool")
    annotation_lines = result.split("\n")

    assert_that(annotation_lines).is_length(2)
    assert_that(annotation_lines[0]).starts_with("::error ")
    assert_that(annotation_lines[1]).starts_with("::warning ")


def test_github_style_no_tool_name(github_style: GitHubStyle) -> None:
    """GitHubStyle works without a tool_name (uses code as title).

    Args:
        github_style: The GitHubStyle formatter instance.
    """
    columns = ["File", "Line", "Column", "Code", "Message", "Severity"]
    rows = [["a.py", "1", "-", "E501", "Too long", "error"]]

    result = github_style.format(columns, rows, tool_name=None)

    assert_that(result).contains("title=E501")


def test_github_style_dash_line_column_omitted(github_style: GitHubStyle) -> None:
    """GitHubStyle omits line and col when they are dashes.

    Args:
        github_style: The GitHubStyle formatter instance.
    """
    columns = ["File", "Line", "Column", "Code", "Message", "Severity"]
    rows = [["a.py", "-", "-", "X", "Msg", "error"]]

    result = github_style.format(columns, rows, tool_name="tool")

    assert_that(result).does_not_contain("line=")
    assert_that(result).does_not_contain("col=")
