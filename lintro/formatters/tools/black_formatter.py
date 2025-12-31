"""Formatter for Black issues."""

from __future__ import annotations

from lintro.enums.output_format import OutputFormat
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.utils.path_utils import normalize_file_path_for_display

FORMAT_MAP = {
    OutputFormat.PLAIN: PlainStyle(),
    OutputFormat.GRID: GridStyle(),
    OutputFormat.MARKDOWN: MarkdownStyle(),
    OutputFormat.HTML: HtmlStyle(),
    OutputFormat.JSON: JsonStyle(),
    OutputFormat.CSV: CsvStyle(),
}


class BlackTableDescriptor:
    """Column layout for Black issues in tabular output."""

    def get_columns(self) -> list[str]:
        """Return ordered column headers for Black output rows.

        Returns:
            list[str]: Column names for the formatted table.
        """
        return ["File", "Line", "Column", "Code", "Severity", "Message"]

    def get_rows(self, issues: list) -> list[list[str]]:
        """Return formatted rows for Black issues.

        Args:
            issues: Parsed Black issues to render.

        Returns:
            list[list[str]]: Table rows with normalized file path and fields.
        """
        rows: list[list[str]] = []
        for issue in issues:
            # For issues without line/column/code/severity (general formatting),
            # show "-" to maintain table structure
            line_str = (
                str(issue.line) if issue.line is not None and issue.line > 0 else "-"
            )
            column_str = (
                str(issue.column)
                if issue.column is not None and issue.column > 0
                else "-"
            )
            code_str = issue.code if issue.code else "-"
            severity_str = issue.severity if issue.severity else "-"
            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    line_str,
                    column_str,
                    code_str,
                    severity_str,
                    issue.message,
                ],
            )
        return rows


def format_black_issues(issues, format: OutputFormat) -> str:
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
    if format == OutputFormat.JSON:
        return formatter.format(columns=columns, rows=rows, tool_name="black")
    return formatter.format(columns=columns, rows=rows)
