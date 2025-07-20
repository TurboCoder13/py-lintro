"""Formatter for Prettier issues."""

from typing import List

from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.parsers.prettier.prettier_issue import PrettierIssue

FORMAT_MAP = {
    "plain": PlainStyle(),
    "grid": GridStyle(),
    "markdown": MarkdownStyle(),
    "html": HtmlStyle(),
    "json": JsonStyle(),
    "csv": CsvStyle(),
}


class PrettierTableDescriptor(TableDescriptor):
    def get_columns(self) -> List[str]:
        return ["File", "Line", "Column", "Code", "Message"]

    def get_rows(self, issues: List[PrettierIssue]) -> List[List[str]]:
        return [
            [
                issue.file,
                str(issue.line) if issue.line is not None else "-",
                str(issue.column) if issue.column is not None else "-",
                issue.code,
                issue.message,
            ]
            for issue in issues
        ]


def format_prettier_issues(issues: List[PrettierIssue], format: str = "grid") -> str:
    """Format a list of Prettier issues using the specified format.

    Args:
        issues: List of Prettier issues to format.
        format: Output format (plain, grid, markdown, html, json, csv).

    Returns:
        Formatted string representation of the issues.
    """
    descriptor = PrettierTableDescriptor()
    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)

    formatter = FORMAT_MAP.get(format, GridStyle())

    # For JSON format, pass tool name
    if format == "json":
        return formatter.format(columns, rows, tool_name="prettier")

    # For other formats, use standard formatting
    return formatter.format(columns, rows)
