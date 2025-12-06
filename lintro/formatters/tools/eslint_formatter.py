"""Formatter for ESLint issues."""

from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.styles.csv import CsvStyle
from lintro.formatters.styles.grid import GridStyle
from lintro.formatters.styles.html import HtmlStyle
from lintro.formatters.styles.json import JsonStyle
from lintro.formatters.styles.markdown import MarkdownStyle
from lintro.formatters.styles.plain import PlainStyle
from lintro.parsers.eslint.eslint_issue import EslintIssue
from lintro.utils.path_utils import normalize_file_path_for_display

FORMAT_MAP = {
    "plain": PlainStyle(),
    "grid": GridStyle(),
    "markdown": MarkdownStyle(),
    "html": HtmlStyle(),
    "json": JsonStyle(),
    "csv": CsvStyle(),
}


class EslintTableDescriptor(TableDescriptor):
    """Describe columns and rows for ESLint issues."""

    def get_columns(self) -> list[str]:
        """Return ordered column headers for the ESLint table.

        Returns:
            list[str]: Column names for the formatted table.
        """
        return ["File", "Line", "Column", "Code", "Severity", "Message"]

    def get_rows(
        self,
        issues: list[EslintIssue],
    ) -> list[list[str]]:
        """Return rows for the ESLint issues table.

        Args:
            issues: Parsed ESLint issues to render.

        Returns:
            list[list[str]]: Table rows with normalized file path and fields.
        """
        rows = []
        for issue in issues:
            severity_str = "error" if issue.severity == 2 else "warning"
            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    str(issue.line),
                    str(issue.column),
                    issue.code,
                    severity_str,
                    issue.message,
                ],
            )
        return rows


def format_eslint_issues(
    issues: list[EslintIssue],
    format: str = "grid",
) -> str:
    """Format ESLint issues with auto-fixable labeling.

    Args:
        issues: List of EslintIssue objects.
        format: Output format identifier (e.g., "grid", "json").

    Returns:
        str: Formatted output string.

    Notes:
        ESLint issues can be auto-fixable if the fixable flag is True.
        For non-JSON formats, issues are split into auto-fixable and not auto-fixable sections.
        JSON returns the combined table for compatibility.
    """
    descriptor = EslintTableDescriptor()
    formatter = FORMAT_MAP.get(format, GridStyle())

    if format == "json":
        columns = descriptor.get_columns()
        rows = descriptor.get_rows(issues)
        return formatter.format(columns=columns, rows=rows, tool_name="eslint")

    # Split issues by fixability
    fixable_issues = [i for i in issues if i.fixable]
    non_fixable_issues = [i for i in issues if not i.fixable]

    sections: list[str] = []
    if fixable_issues:
        columns = descriptor.get_columns()
        rows = descriptor.get_rows(fixable_issues)
        table = formatter.format(columns=columns, rows=rows)
        sections.append("Auto-fixable issues\n" + table)
    if non_fixable_issues:
        columns = descriptor.get_columns()
        rows = descriptor.get_rows(non_fixable_issues)
        table = formatter.format(columns=columns, rows=rows)
        sections.append("Not auto-fixable issues\n" + table)

    if not sections:
        return "No issues found."

    return "\n\n".join(sections)

