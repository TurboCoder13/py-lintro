"""Formatter for darglint issues."""

from lintro.enums.output_format import OutputFormat
from lintro.formatters.core.format_registry import get_style
from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.parsers.darglint.darglint_issue import DarglintIssue
from lintro.utils.path_utils import normalize_file_path_for_display


class DarglintTableDescriptor(TableDescriptor):
    """Describe columns and rows for Darglint issues."""

    def get_columns(self) -> list[str]:
        """Return column headers for the Darglint issues table.

        Returns:
            list[str]: Column names for the formatted table.
        """
        return ["File", "Line", "Code", "Message"]

    def get_rows(
        self,
        issues: list[DarglintIssue],
    ) -> list[list[str]]:
        """Return rows for the Darglint table.

        Args:
            issues: Parsed Darglint issues to format.

        Returns:
            list[list[str]]: Table rows with normalized path, line, code, message.
        """
        rows = []
        for issue in issues:
            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    str(issue.line),
                    issue.code,
                    issue.message,
                ],
            )
        return rows


def format_darglint_issues(
    issues: list[DarglintIssue],
    format: OutputFormat = OutputFormat.GRID,
) -> str:
    """Format a list of Darglint issues using the specified format.

    Args:
        issues: List of Darglint issues to format.
        format: Output format (plain, grid, markdown, html, json, csv).

    Returns:
        str: Formatted string representation of the issues.
    """
    descriptor = DarglintTableDescriptor()
    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)

    formatter = get_style(format)

    # For JSON format, pass tool name
    if format == OutputFormat.JSON:
        formatted_table = formatter.format(
            columns=columns,
            rows=rows,
            tool_name="darglint",
        )
    else:
        # For other formats, use standard formatting
        formatted_table = formatter.format(columns=columns, rows=rows)

    return formatted_table
