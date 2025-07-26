"""Formatter for ruff issues."""

from typing import List

import click

from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.parsers.ruff.ruff_issue import RuffFormatIssue, RuffIssue
from lintro.utils.path_utils import normalize_file_path_for_display

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

    def get_rows(self, issues: List[RuffIssue | RuffFormatIssue]) -> List[List[str]]:
        rows = []
        for issue in issues:
            if isinstance(issue, RuffIssue):
                # Linting issue
                rows.append(
                    [
                        normalize_file_path_for_display(issue.file),
                        str(issue.line),
                        str(issue.column),
                        issue.code,
                        issue.message,
                        "Yes" if issue.fixable else "No",
                    ]
                )
            elif isinstance(issue, RuffFormatIssue):
                # Formatting issue
                rows.append(
                    [
                        normalize_file_path_for_display(issue.file),
                        "-",
                        "-",
                        "FORMAT",
                        "Would reformat file",
                        "Yes",
                    ]
                )
        return rows


def format_ruff_issues(
    issues: List[RuffIssue | RuffFormatIssue], format: str = "grid"
) -> str:
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
        formatted_table = formatter.format(columns, rows, tool_name="ruff")
    else:
        # For other formats, use standard formatting
        formatted_table = formatter.format(columns, rows)

    # Add formatted summary information that matches the console logger style
    if issues:
        # Separate linting and formatting issues
        lint_issues = [issue for issue in issues if isinstance(issue, RuffIssue)]
        format_issues = [
            issue for issue in issues if isinstance(issue, RuffFormatIssue)
        ]

        summary_lines = []

        # Calculate total issues and fixable count
        total_issues = len(lint_issues) + len(format_issues)
        total_fixable = sum(1 for issue in lint_issues if issue.fixable) + len(
            format_issues
        )

        # Use console logger style formatting with colors
        error_msg = click.style(f"✗ Found {total_issues} issues", fg="red")
        summary_lines.append(error_msg)
        if total_fixable > 0:
            fixable_msg = click.style(
                f"⚠️  {total_fixable} can be auto fixed with `lintro fmt`", fg="yellow"
            )
            summary_lines.append(fixable_msg)

        # Combine table and summary
        if summary_lines:
            return f"{formatted_table}\n\n{chr(10).join(summary_lines)}"

    return formatted_table
