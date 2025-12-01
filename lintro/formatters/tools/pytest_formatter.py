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

# Maximum message length before truncation (reasonable for terminal widths)
MAX_MESSAGE_LENGTH: int = 100

FORMAT_MAP = {
    "plain": PlainStyle(),
    "grid": GridStyle(),
    "markdown": MarkdownStyle(),
    "html": HtmlStyle(),
    "json": JsonStyle(),
    "csv": CsvStyle(),
}


class PytestFailuresTableDescriptor(TableDescriptor):
    """Describe columns and rows for pytest failed/error issues."""

    def get_columns(self) -> list[str]:
        """Return ordered column headers for the pytest failures table.

        Returns:
            list[str]: Column names for the formatted table.
        """
        return ["File", "Status", "Error"]

    def get_rows(
        self,
        issues: list[PytestIssue],
    ) -> list[list[str]]:
        """Return rows for the pytest failures table.

        Args:
            issues: Parsed pytest issues to render.

        Returns:
            list[list[str]]: Table rows with normalized file path and fields.
        """
        rows = []
        for issue in issues:
            # Only show failed/error tests
            if issue.test_status not in ("FAILED", "ERROR"):
                continue

            message = str(issue.message) if issue.message is not None else ""
            truncated_message = (
                f"{message[:MAX_MESSAGE_LENGTH]}..."
                if len(message) > MAX_MESSAGE_LENGTH + 3
                else message
            )

            status_emoji = "❌ FAIL" if issue.test_status == "FAILED" else "⚠️ ERROR"

            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    status_emoji,
                    truncated_message,
                ],
            )
        return rows


class PytestSkippedTableDescriptor(TableDescriptor):
    """Describe columns and rows for pytest skipped issues."""

    def get_columns(self) -> list[str]:
        """Return ordered column headers for the pytest skipped table.

        Returns:
            list[str]: Column names for the formatted table.
        """
        return ["File", "Test", "Skip Reason"]

    def get_rows(
        self,
        issues: list[PytestIssue],
    ) -> list[list[str]]:
        """Return rows for the pytest skipped table.

        Args:
            issues: Parsed pytest issues to render.

        Returns:
            list[list[str]]: Table rows with normalized file path and fields.
        """
        rows = []
        for issue in issues:
            # Only show skipped tests
            if issue.test_status != "SKIPPED":
                continue

            message = str(issue.message) if issue.message is not None else ""
            truncated_message = (
                f"{message[:MAX_MESSAGE_LENGTH]}..."
                if len(message) > MAX_MESSAGE_LENGTH + 3
                else message
            )

            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    issue.test_name or "Unknown",
                    truncated_message,
                ],
            )
        return rows


def format_pytest_failures(
    issues: list[PytestIssue],
    format: str = "grid",
) -> str:
    """Format pytest failures and errors into a table.

    Args:
        issues: List of pytest issues to format.
        format: Output format (plain, grid, markdown, html, json, csv).

    Returns:
        str: Formatted string with pytest failures table.
    """
    descriptor = PytestFailuresTableDescriptor()
    formatter = FORMAT_MAP.get(format, GridStyle())

    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)

    # Always return a table structure, even if empty
    return formatter.format(
        columns=columns,
        rows=rows,
    )


def format_pytest_skipped(
    issues: list[PytestIssue],
    format: str = "grid",
) -> str:
    """Format pytest skipped tests into a table.

    Args:
        issues: List of pytest issues to format.
        format: Output format (plain, grid, markdown, html, json, csv).

    Returns:
        str: Formatted string with pytest skipped tests table.
    """
    descriptor = PytestSkippedTableDescriptor()
    formatter = FORMAT_MAP.get(format, GridStyle())

    columns = descriptor.get_columns()
    rows = descriptor.get_rows(issues)

    # Always return a table structure, even if empty
    return formatter.format(
        columns=columns,
        rows=rows,
    )


def format_pytest_issues(
    issues: list[PytestIssue],
    format: str = "grid",
) -> str:
    """Format pytest issues into tables for failures and skipped tests.

    Args:
        issues: List of pytest issues to format.
        format: Output format (plain, grid, markdown, html, json, csv).

    Returns:
        str: Formatted string with pytest issues tables.
    """
    output_parts = []

    # Format failures table
    failures_table = format_pytest_failures(issues, format)
    if failures_table.strip():
        output_parts.append("Test Failures:")
        output_parts.append(failures_table)

    # Format skipped tests table
    skipped_table = format_pytest_skipped(issues, format)
    if skipped_table.strip():
        if output_parts:
            output_parts.append("")  # Add blank line between tables
        output_parts.append("Skipped Tests:")
        output_parts.append(skipped_table)

    return "\n".join(output_parts)
