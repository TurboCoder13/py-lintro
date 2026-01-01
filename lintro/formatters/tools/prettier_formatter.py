"""Formatter for Prettier issues."""

from lintro.enums.output_format import OutputFormat
from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.parsers.prettier.prettier_issue import PrettierIssue
from lintro.utils.path_utils import normalize_file_path_for_display

FORMAT_MAP = {
    OutputFormat.PLAIN: PlainStyle(),
    OutputFormat.GRID: GridStyle(),
    OutputFormat.MARKDOWN: MarkdownStyle(),
    OutputFormat.HTML: HtmlStyle(),
    OutputFormat.JSON: JsonStyle(),
    OutputFormat.CSV: CsvStyle(),
}


class PrettierTableDescriptor(TableDescriptor):
    """Describe columns and rows for Prettier issues."""

    def get_columns(self) -> list[str]:
        """Return ordered column headers for the Prettier table.

        Returns:
            list[str]: Column names for the formatted table.
        """
        return ["File", "Line", "Column", "Code", "Message"]

    def get_rows(
        self,
        issues: list[PrettierIssue],
    ) -> list[list[str]]:
        """Return rows for the Prettier issues table.

        Args:
            issues: Parsed Prettier issues to render.

        Returns:
            list[list[str]]: Table rows with normalized file path and fields.
        """
        rows = []
        for issue in issues:
            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    str(issue.line) if issue.line > 0 else "-",
                    str(issue.column) if issue.column > 0 else "-",
                    issue.code,
                    issue.message,
                ],
            )
        return rows


def format_prettier_issues(
    issues: list[PrettierIssue],
    format: OutputFormat = OutputFormat.GRID,
) -> str:
    """Format Prettier issues with auto-fixable labeling.

    Args:
        issues: List of PrettierIssue objects.
        format: Output format identifier (e.g., "grid", "json").

    Returns:
        str: Formatted output string.

    Notes:
        All Prettier issues are auto-fixable by running `lintro format`.
        For non-JSON formats, a single section is labeled as auto-fixable.
        JSON returns the combined table for compatibility.
    """
    descriptor = PrettierTableDescriptor()
    formatter = FORMAT_MAP.get(format, GridStyle())

    if format == OutputFormat.JSON:
        columns = descriptor.get_columns()
        rows = descriptor.get_rows(issues)
        return formatter.format(columns=columns, rows=rows, tool_name="prettier")

    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)
    table = formatter.format(columns=columns, rows=rows)
    if not rows:
        return table
    return "Auto-fixable issues\n" + table
