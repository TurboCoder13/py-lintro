"""Formatter for mypy issues."""

from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.parsers.mypy.mypy_issue import MypyIssue
from lintro.utils.path_utils import normalize_file_path_for_display

FORMAT_MAP = {
    "plain": PlainStyle(),
    "grid": GridStyle(),
    "markdown": MarkdownStyle(),
    "html": HtmlStyle(),
    "json": JsonStyle(),
    "csv": CsvStyle(),
}


class MypyTableDescriptor(TableDescriptor):
    """Describe columns and rows for mypy issues."""

    def get_columns(self) -> list[str]:
        """Return ordered column headers for the mypy table.

        Returns:
            Column headers displayed in mypy issue tables.
        """
        return ["File", "Line", "Column", "Code", "Message"]

    def get_rows(
        self,
        issues: list[MypyIssue],
    ) -> list[list[str]]:
        """Return rows for the mypy issues table.

        Args:
            issues: Parsed mypy issues.

        Returns:
            Tabular rows ready for rendering by the selected formatter.
        """
        rows: list[list[str]] = []
        for issue in issues:
            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    str(issue.line),
                    str(issue.column),
                    issue.code or "",
                    issue.message,
                ],
            )
        return rows


def format_mypy_issues(
    issues: list[MypyIssue],
    format: str = "grid",
) -> str:
    """Format mypy issues into the requested output style.

    Args:
        issues: Parsed mypy issues to render.
        format: Output format name (grid, markdown, html, json, csv, plain).

    Returns:
        A formatted string representing the issues in the requested style.
    """
    descriptor = MypyTableDescriptor()
    formatter = FORMAT_MAP.get(format, GridStyle())

    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)

    return formatter.format(columns=columns, rows=rows)
