"""Formatter for Black issues."""

from __future__ import annotations

from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.utils.path_utils import normalize_file_path_for_display

FORMAT_MAP = {
    "plain": PlainStyle(),
    "grid": GridStyle(),
    "markdown": MarkdownStyle(),
    "html": HtmlStyle(),
    "json": JsonStyle(),
    "csv": CsvStyle(),
}


class BlackTableDescriptor:
    """Column layout for Black issues in tabular output."""

    def get_columns(self) -> list[str]:
        """Return ordered column headers for Black output rows.

        Returns:
            list[str]: Column names for the formatted table.
        """
        return ["File", "Message"]

    def get_rows(self, issues: list) -> list[list[str]]:
        """Return formatted rows for Black issues.

        Args:
            issues: Parsed Black issues to render.

        Returns:
            list[list[str]]: Table rows with normalized file paths and messages.
        """
        rows: list[list[str]] = []
        for issue in issues:
            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    issue.message,
                ],
            )
        return rows


def format_black_issues(issues, format: str) -> str:
    """Format Black issues according to the chosen style.

    Args:
        issues: Parsed Black issues.
        format: Output style identifier.

    Returns:
        str: Rendered table string.
    """
    descriptor = BlackTableDescriptor()
    formatter = FORMAT_MAP.get(format, GridStyle())
    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)
    if format == "json":
        return formatter.format(columns=columns, rows=rows, tool_name="black")
    return formatter.format(columns=columns, rows=rows)
