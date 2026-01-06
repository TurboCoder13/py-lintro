"""Formatter for actionlint issues."""

from lintro.formatters.core.format_registry import get_style
from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.styles.json import JsonStyle
from lintro.parsers.actionlint.actionlint_issue import ActionlintIssue
from lintro.utils.path_utils import normalize_file_path_for_display


class ActionlintTableDescriptor(TableDescriptor):
    """Table descriptor for rendering Actionlint issues.

    Provides the column schema and row extraction logic so any output style
    can render a uniform table across formats (grid, markdown, html, csv, json).
    """

    def get_columns(self) -> list[str]:
        """Return the ordered column headers for Actionlint issues.

        Returns:
            list[str]: Column names used by formatters.
        """
        return ["File", "Line", "Column", "Level", "Code", "Message"]

    def get_rows(self, issues: list[ActionlintIssue]) -> list[list[str]]:
        """Convert Actionlint issues to a list of row values.

        Args:
            issues: Parsed Actionlint issues to render.

        Returns:
            list[list[str]]: One row per issue matching the column order.
        """
        rows: list[list[str]] = []
        for issue in issues:
            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    str(issue.line),
                    str(issue.column),
                    issue.level,
                    issue.code or "",
                    issue.message,
                ],
            )
        return rows


def format_actionlint_issues(
    issues: list[ActionlintIssue],
    format: str = "grid",
) -> str:
    """Format Actionlint issues using the selected output style.

    Args:
        issues: Parsed Actionlint issues to format.
        format: Output style key (plain, grid, markdown, html, json, csv).

    Returns:
        str: Rendered table content for the chosen style.
    """
    descriptor = ActionlintTableDescriptor()
    formatter = get_style(format)
    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)
    # JsonStyle may accept tool_name but others do not; keep simple
    if isinstance(formatter, JsonStyle):
        return formatter.format(columns=columns, rows=rows, tool_name="actionlint")
    return formatter.format(columns=columns, rows=rows)
