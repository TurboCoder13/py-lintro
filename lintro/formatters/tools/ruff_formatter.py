"""Formatter for ruff issues."""

from collections.abc import Sequence

from lintro.enums.output_format import OutputFormat
from lintro.formatters.core.format_registry import get_format_map, get_style
from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.parsers.ruff.ruff_issue import RuffFormatIssue, RuffIssue
from lintro.utils.path_utils import normalize_file_path_for_display

# Use shared format registry instead of duplicating style instances
FORMAT_MAP = get_format_map()


class RuffTableDescriptor(TableDescriptor):
    """Describe columns and rows for Ruff issues."""

    def get_columns(self) -> list[str]:
        """Return ordered column headers for the Ruff table.

        Returns:
            list[str]: Column names for the formatted table.
        """
        return ["File", "Line", "Column", "Code", "Message"]

    def get_rows(
        self,
        issues: Sequence[RuffIssue | RuffFormatIssue],
    ) -> list[list[str]]:
        """Return rows for the Ruff issues table.

        Args:
            issues: Parsed Ruff issues to render.

        Returns:
            list[list[str]]: Table rows with normalized file path and fields.
        """
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
                    ],
                )
            elif isinstance(issue, RuffFormatIssue):
                # From Lintro's perspective, fmt applies both lint fixes and
                # formatting, so formatting entries are auto-fixable by fmt.
                rows.append(
                    [
                        normalize_file_path_for_display(issue.file),
                        "-",
                        "-",
                        "FORMAT",
                        "Would reformat file",
                    ],
                )
        return rows


def format_ruff_issues(
    issues: Sequence[RuffIssue | RuffFormatIssue],
    format: str | OutputFormat = "grid",
) -> str:
    """Format Ruff issues, split into auto-fixable and not auto-fixable tables.

    For JSON format, return a single combined table (backwards compatible).

    Args:
        issues: List of Ruff issues to format.
        format: Output format (plain, grid, markdown, html, json, csv).

    Returns:
        str: Formatted string (one or two tables depending on format).
    """
    from lintro.enums.output_format import normalize_output_format

    normalized_format = normalize_output_format(format or "grid")
    descriptor = RuffTableDescriptor()
    formatter = get_style(normalized_format)

    # Partition issues
    fixable_issues: list[RuffIssue | RuffFormatIssue] = []
    non_fixable_issues: list[RuffIssue] = []

    for issue in issues:
        if (
            isinstance(issue, RuffFormatIssue)
            or isinstance(issue, RuffIssue)
            and issue.fixable
        ):
            fixable_issues.append(issue)
        elif isinstance(issue, RuffIssue):
            non_fixable_issues.append(issue)

    # JSON: keep a single table for compatibility
    if normalized_format == OutputFormat.JSON:
        columns = descriptor.get_columns()
        rows = descriptor.get_rows(issues)
        return formatter.format(
            columns=columns,
            rows=rows,
            tool_name="ruff",
        )

    sections: list[str] = []

    # Auto-fixable section
    if fixable_issues:
        columns_f = descriptor.get_columns()
        rows_f = descriptor.get_rows(fixable_issues)
        table_f = formatter.format(columns=columns_f, rows=rows_f)
        sections.append("Auto-fixable issues\n" + table_f)

    # Not auto-fixable section
    if non_fixable_issues:
        columns_u = descriptor.get_columns()
        rows_u = descriptor.get_rows(non_fixable_issues)
        table_u = formatter.format(columns=columns_u, rows=rows_u)
        sections.append("Not auto-fixable issues\n" + table_u)

    # If neither, return empty table structure
    if not sections:
        columns = descriptor.get_columns()
        return formatter.format(columns=columns, rows=[])

    return "\n\n".join(sections)
