"""Formatter for darglint issues."""

from typing import List

import click

from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.parsers.darglint.darglint_issue import DarglintIssue
from lintro.utils.path_utils import normalize_file_path_for_display

FORMAT_MAP = {
    "plain": PlainStyle(),
    "grid": GridStyle(),
    "markdown": MarkdownStyle(),
    "html": HtmlStyle(),
    "json": JsonStyle(),
    "csv": CsvStyle(),
}


class DarglintTableDescriptor(TableDescriptor):
    def get_columns(self) -> List[str]:
        return ["File", "Line", "Code", "Message"]

    def get_rows(self, issues: List[DarglintIssue]) -> List[List[str]]:
        return [
            [
                normalize_file_path_for_display(issue.file),
                str(issue.line),
                issue.code,
                issue.message,
            ]
            for issue in issues
        ]


def format_darglint_issues(issues: List[DarglintIssue], format: str = "grid") -> str:
    """Format a list of Darglint issues using the specified format.

    Args:
        issues: List of Darglint issues to format.
        format: Output format (plain, grid, markdown, html, json, csv).

    Returns:
        Formatted string representation of the issues.
    """
    descriptor = DarglintTableDescriptor()
    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)

    formatter = FORMAT_MAP.get(format, GridStyle())

    # For JSON format, pass tool name
    if format == "json":
        return formatter.format(columns, rows, tool_name="darglint")

    # For other formats, add status messages
    formatted_table = formatter.format(columns, rows)

    if issues:
        # Add status message in console logger style
        error_msg = click.style(f"✗ Found {len(issues)} issues", fg="red")
        return f"{formatted_table}\n\n{error_msg}"

    return formatted_table
