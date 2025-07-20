"""Formatter for ruff issues."""

from typing import List

from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.parsers.ruff.ruff_issue import RuffIssue

FORMAT_MAP = {
    "plain": PlainStyle(),
    "grid": GridStyle(),
    "markdown": MarkdownStyle(),
    "html": HtmlStyle(),
    "json": JsonStyle(),
    "csv": CsvStyle(),
}


class RuffTableDescriptor(TableDescriptor):
    def get_columns(self) -> List[str]:
        return ["File", "Line", "Column", "Code", "Message", "Fixable"]

    def get_rows(self, issues: List[RuffIssue]) -> List[List[str]]:
        return [
            [
                issue.file,
                str(issue.line),
                str(issue.column),
                issue.code,
                issue.message,
                "Yes" if issue.fixable else "No",
            ]
            for issue in issues
        ]


def format_ruff_issues(issues: List[RuffIssue], format: str = "grid") -> str:
    """Format a list of Ruff issues using the specified format.

    Args:
        issues: List of Ruff issues to format.
        format: Output format (plain, grid, markdown, html, json, csv).

    Returns:
        Formatted string representation of the issues.
    """
    descriptor = RuffTableDescriptor()
    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)

    formatter = FORMAT_MAP.get(format, GridStyle())

    # For JSON format, pass tool name
    if format == "json":
        return formatter.format(columns, rows, tool_name="ruff")

    # For other formats, use standard formatting
    return formatter.format(columns, rows)
