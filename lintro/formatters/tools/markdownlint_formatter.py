"""Formatter for Markdownlint issues."""

from lintro.enums.output_format import OutputFormat, normalize_output_format
from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.parsers.markdownlint.markdownlint_issue import MarkdownlintIssue
from lintro.utils.path_utils import normalize_file_path_for_display


class MarkdownlintTableDescriptor(TableDescriptor):
    """Describe columns and rows for Markdownlint issues."""

    def get_columns(self) -> list[str]:
        """Return ordered column headers for the Markdownlint table.

        Returns:
            list[str]: Column names for the formatted table.
        """
        return ["File", "Line", "Column", "Code", "Message"]

    def get_rows(
        self,
        issues: list[MarkdownlintIssue],
    ) -> list[list[str]]:
        """Return rows for the Markdownlint issues table.

        Args:
            issues: Parsed Markdownlint issues to render.

        Returns:
            list[list[str]]: Table rows with normalized file path and fields.
        """
        rows = []
        for issue in issues:
            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    str(issue.line),
                    str(issue.column) if issue.column is not None else "-",
                    issue.code,
                    issue.message,
                ],
            )
        return rows


def format_markdownlint_issues(
    issues: list[MarkdownlintIssue],
    format: str = "grid",
    *,
    tool_name: str = "markdownlint",
) -> str:
    """Format Markdownlint issues to the given style.

    Args:
        issues: List of MarkdownlintIssue instances.
        format: Output style identifier.
        tool_name: Tool name for JSON metadata.

    Returns:
        str: Rendered string for the issues table.
    """
    descriptor = MarkdownlintTableDescriptor()
    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)

    if not rows:
        return "No issues found."

    style = normalize_output_format(format or "grid")
    if style == OutputFormat.GRID:
        return GridStyle().format(columns=columns, rows=rows)
    if style == OutputFormat.PLAIN:
        return PlainStyle().format(columns=columns, rows=rows)
    if style == OutputFormat.MARKDOWN:
        return MarkdownStyle().format(columns=columns, rows=rows)
    if style == OutputFormat.HTML:
        return HtmlStyle().format(columns=columns, rows=rows)
    if style == OutputFormat.JSON:
        return JsonStyle().format(columns=columns, rows=rows, tool_name=tool_name)
    if style == OutputFormat.CSV:
        return CsvStyle().format(columns=columns, rows=rows)

    return GridStyle().format(columns=columns, rows=rows)
