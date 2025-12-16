"""Clippy table formatting utilities."""

from __future__ import annotations

from typing import Any

from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.parsers.clippy.clippy_issue import ClippyIssue
from lintro.utils.path_utils import normalize_file_path_for_display


class ClippyTableDescriptor(TableDescriptor):
    """Describe clippy issue columns and row extraction."""

    def get_columns(self) -> list[str]:
        """Return ordered column headers for the Clippy table.

        Returns:
            list[str]: Column names for the formatted table.
        """
        return ["File", "Line", "Column", "Code", "Level", "Message"]

    def get_rows(
        self,
        issues: list[ClippyIssue],
    ) -> list[list[Any]]:
        """Return rows for the Clippy issues table.

        Args:
            issues: Parsed Clippy issues to render.

        Returns:
            list[list[Any]]: Table rows with normalized file path and fields.
        """
        rows: list[list[Any]] = []
        for issue in issues:
            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    issue.line,
                    issue.column,
                    issue.code or "",
                    issue.level or "",
                    issue.message,
                ],
            )
        return rows


def format_clippy_issues(
    issues: list[ClippyIssue],
    format: str = "grid",
) -> str:
    """Format clippy issues to the given style.

    Args:
        issues: List of ClippyIssue instances.
        format: Output style identifier.

    Returns:
        Rendered string for the issues table.
    """
    descriptor = ClippyTableDescriptor()
    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)

    if not rows:
        return "No issues found."

    style = (format or "grid").lower()
    if style == "grid":
        return GridStyle().format(columns=columns, rows=rows)
    if style == "plain":
        return PlainStyle().format(columns=columns, rows=rows)
    if style == "markdown":
        return MarkdownStyle().format(columns=columns, rows=rows)
    if style == "html":
        return HtmlStyle().format(columns=columns, rows=rows)
    if style == "json":
        return JsonStyle().format(columns=columns, rows=rows, tool_name="clippy")
    if style == "csv":
        return CsvStyle().format(columns=columns, rows=rows)

    return GridStyle().format(columns=columns, rows=rows)
