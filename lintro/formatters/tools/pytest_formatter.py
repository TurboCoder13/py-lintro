"""Formatter for pytest issues."""

from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.parsers.pytest.pytest_issue import PytestIssue
from lintro.utils.path_utils import normalize_file_path_for_display

FORMAT_MAP = {
    "plain": PlainStyle(),
    "grid": GridStyle(),
    "markdown": MarkdownStyle(),
    "html": HtmlStyle(),
    "json": JsonStyle(),
    "csv": CsvStyle(),
}


class PytestTableDescriptor(TableDescriptor):
    """Describe columns and rows for pytest issues."""

    def get_columns(self) -> list[str]:
        """Return ordered column headers for the pytest table.

        Returns:
            list[str]: Column names for the formatted table.
        """
        return ["File", "Line", "Test Name", "Status", "Message"]

    def get_rows(
        self,
        issues: list[PytestIssue],
    ) -> list[list[str]]:
        """Return rows for the pytest issues table.

        Args:
            issues: Parsed pytest issues to render.

        Returns:
            list[list[str]]: Table rows with normalized file path and fields.
        """
        rows = []
        for issue in issues:
            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    str(issue.line) if issue.line > 0 else "-",
                    issue.test_name or "-",
                    issue.test_status,
                    issue.message[:100] + "..." if len(issue.message) > 100 else issue.message,
                ],
            )
        return rows


def format_pytest_issues(
    issues: list[PytestIssue],
    format: str = "grid",
) -> str:
    """Format pytest issues into a table.

    Args:
        issues: List of pytest issues to format.
        format: Output format (plain, grid, markdown, html, json, csv).

    Returns:
        str: Formatted string with pytest issues table.
    """
    descriptor = PytestTableDescriptor()
    formatter = FORMAT_MAP.get(format, GridStyle())

    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)

    # Always return a table structure, even if empty
    return formatter.format(
        columns=columns,
        rows=rows,
    )
