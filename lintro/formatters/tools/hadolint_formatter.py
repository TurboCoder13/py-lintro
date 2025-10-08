"""Hadolint table formatting utilities."""

from __future__ import annotations

from typing import Any

from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.parsers.hadolint.hadolint_issue import HadolintIssue
from lintro.utils.path_utils import normalize_file_path_for_display


class HadolintTableDescriptor(TableDescriptor):
    """Describe hadolint issue columns and row extraction."""

    def get_columns(self) -> list[str]:
        """Return ordered column headers for the Hadolint table.

        Returns:
            list[str]: Column names for the formatted table.
        """
        return [
            "File",
            "Line",
            "Column",
            "Level",
            "Code",
            "Message",
        ]

    def get_rows(
        self,
        issues: list[HadolintIssue],
    ) -> list[list[Any]]:
        """Return rows for the Hadolint issues table.

        Args:
            issues: Parsed Hadolint issues to render.

        Returns:
            list[list[Any]]: Table rows with normalized file path and fields.
        """
        rows: list[list[Any]] = []
        for issue in issues:
            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    issue.line,
                    issue.column if getattr(issue, "column", None) is not None else "",
                    issue.level,
                    issue.code,
                    issue.message,
                ],
            )
        return rows


def format_hadolint_issues(
    issues: list[HadolintIssue],
    format: str = "grid",
) -> str:
    """Format hadolint issues to the given style.

    Args:
        issues: List of HadolintIssue instances.
        format: Output style identifier.

    Returns:
        Rendered string for the issues table.
    """
    descriptor = HadolintTableDescriptor()
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
        return JsonStyle().format(columns=columns, rows=rows, tool_name="hadolint")
    if style == "csv":
        return CsvStyle().format(columns=columns, rows=rows)

    return GridStyle().format(columns=columns, rows=rows)
