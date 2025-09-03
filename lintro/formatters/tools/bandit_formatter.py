"""Bandit formatter for security issue output."""

from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.parsers.bandit.bandit_issue import BanditIssue
from lintro.utils.path_utils import normalize_file_path_for_display


class BanditTableDescriptor(TableDescriptor):
    """Table descriptor for Bandit security issues."""

    def get_columns(self) -> list[str]:
        """Get column headers for Bandit issues table.

        Returns:
            list[str]: List of column headers.
        """
        return ["File", "Line", "Test ID", "Severity", "Confidence", "Issue"]

    def get_rows(self, issues: list[BanditIssue]) -> list[list[str]]:
        """Convert Bandit issues to table rows.

        Args:
            issues: list[BanditIssue]: List of Bandit issues.

        Returns:
            list[list[str]]: List of table rows.
        """
        rows = []
        for issue in issues:
            # Get severity icon
            severity_icon = self._get_severity_icon(issue.issue_severity)

            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    str(issue.line),
                    issue.test_id,
                    f"{severity_icon} {issue.issue_severity}",
                    issue.issue_confidence,
                    issue.issue_text,
                ],
            )
        return rows

    def _get_severity_icon(self, severity: str) -> str:
        """Get icon for severity level.

        Args:
            severity: str: Severity level.

        Returns:
            str: Icon character.
        """
        return {
            "HIGH": "🔴",
            "MEDIUM": "🟠",
            "LOW": "🟡",
            "UNKNOWN": "⚪",
        }.get(severity.upper(), "⚪")


def format_bandit_issues(
    issues: list[BanditIssue],
    format: str = "grid",
) -> str:
    """Format Bandit issues using the appropriate output style.

    Args:
        issues: list[BanditIssue]: List of Bandit issues to format.
        format: str: Output format (grid, plain, markdown, html, json, csv).

    Returns:
        str: Formatted issues string.
    """
    from lintro.formatters.styles.csv import CsvStyle
    from lintro.formatters.styles.grid import GridStyle
    from lintro.formatters.styles.html import HtmlStyle
    from lintro.formatters.styles.json import JsonStyle
    from lintro.formatters.styles.markdown import MarkdownStyle
    from lintro.formatters.styles.plain import PlainStyle

    style_map = {
        "grid": GridStyle(),
        "plain": PlainStyle(),
        "markdown": MarkdownStyle(),
        "html": HtmlStyle(),
        "json": JsonStyle(),
        "csv": CsvStyle(),
    }

    style_key = (format or "grid").lower()
    style = style_map.get(style_key, GridStyle())
    descriptor = BanditTableDescriptor()

    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)

    if style_key == "json":
        return style.format(columns=columns, rows=rows, tool_name="bandit")
    return style.format(columns=columns, rows=rows)
