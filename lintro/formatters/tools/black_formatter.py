"""Formatter for Black issues."""

from __future__ import annotations

from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.parsers.black.black_issue import BlackIssue
from lintro.utils.path_utils import normalize_file_path_for_display

FORMAT_MAP = {
    "plain": PlainStyle(),
    "grid": GridStyle(),
    "markdown": MarkdownStyle(),
    "html": HtmlStyle(),
    "json": JsonStyle(),
    "csv": CsvStyle(),
}


class BlackTableDescriptor(TableDescriptor):
    def get_columns(self) -> list[str]:
        return ["File", "Message"]

    def get_rows(self, issues: list[BlackIssue]) -> list[list[str]]:
        rows: list[list[str]] = []
        for issue in issues:
            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    issue.message,
                ],
            )
        return rows


def format_black_issues(issues: list[BlackIssue], format: str = "grid") -> str:
    descriptor = BlackTableDescriptor()
    formatter = FORMAT_MAP.get(format, GridStyle())
    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)
    if format == "json":
        return formatter.format(columns=columns, rows=rows, tool_name="black")
    return formatter.format(columns=columns, rows=rows)
