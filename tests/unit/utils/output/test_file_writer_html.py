"""Unit tests for write_output_file function - HTML format.

Tests verify HTML output structure with proper elements and XSS prevention.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from assertpy import assert_that

from lintro.enums.action import Action
from lintro.enums.output_format import OutputFormat
from lintro.utils.output.file_writer import write_output_file

if TYPE_CHECKING:
    from collections.abc import Callable

    from .conftest import MockIssue, MockToolResult


def test_write_html_file_creates_valid_structure(
    tmp_path: Path,
    sample_results_empty: list[MockToolResult],
) -> None:
    """Verify HTML file contains proper document structure with headers and tables.

    Args:
        tmp_path: Temporary directory path for test output.
        sample_results_empty: Mock tool results with no issues.
    """
    output_path = tmp_path / "report.html"

    write_output_file(
        output_path=str(output_path),
        output_format=OutputFormat.HTML,
        all_results=sample_results_empty,  # type: ignore[arg-type]
        action=Action.CHECK,
        total_issues=0,
        total_fixed=0,
    )

    assert_that(output_path.exists()).is_true()
    content = output_path.read_text()

    assert_that(content).contains("<html>")
    assert_that(content).contains("</html>")
    assert_that(content).contains("<h1>Lintro Report</h1>")
    assert_that(content).contains("<h2>Summary</h2>")
    assert_that(content).contains("<table")


def test_write_html_file_includes_issue_table(
    tmp_path: Path,
    sample_results_with_issues: list[MockToolResult],
) -> None:
    """Verify HTML output includes issues in table cells with proper structure.

    Args:
        tmp_path: Temporary directory path for test output.
        sample_results_with_issues: Mock tool results containing issues.
    """
    output_path = tmp_path / "report.html"

    write_output_file(
        output_path=str(output_path),
        output_format=OutputFormat.HTML,
        all_results=sample_results_with_issues,  # type: ignore[arg-type]
        action=Action.CHECK,
        total_issues=1,
        total_fixed=0,
    )

    content = output_path.read_text()

    assert_that(content).contains("<td>src/main.py</td>")
    assert_that(content).contains("<td>10</td>")
    assert_that(content).contains("<td>E001</td>")
    assert_that(content).contains("<td>Test error</td>")


def test_write_html_file_escapes_xss_characters(
    tmp_path: Path,
    mock_tool_result_factory: Callable[..., MockToolResult],
    mock_issue_factory: Callable[..., MockIssue],
) -> None:
    """Verify HTML special characters are escaped to prevent XSS vulnerabilities.

    Args:
        tmp_path: Temporary directory path for test output.
        mock_tool_result_factory: Factory for creating mock tool results.
        mock_issue_factory: Factory for creating mock issues.
    """
    output_path = tmp_path / "report.html"
    results = [
        mock_tool_result_factory(
            name="<script>alert('xss')</script>",
            issues_count=1,
            issues=[mock_issue_factory(message="<b>test</b>")],
        ),
    ]

    write_output_file(
        output_path=str(output_path),
        output_format=OutputFormat.HTML,
        all_results=results,  # type: ignore[arg-type]
        action=Action.CHECK,
        total_issues=1,
        total_fixed=0,
    )

    content = output_path.read_text()

    # Script tags should be escaped, not rendered
    assert_that(content).does_not_contain("<script>")
    assert_that(content).contains("&lt;script&gt;")
    assert_that(content).contains("&lt;b&gt;test&lt;/b&gt;")
