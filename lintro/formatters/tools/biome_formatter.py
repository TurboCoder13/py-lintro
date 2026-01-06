"""Formatter for Biome issues."""

from lintro.enums.output_format import OutputFormat
from lintro.formatters.core.format_registry import get_style
from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.parsers.biome.biome_issue import BiomeIssue
from lintro.utils.path_utils import normalize_file_path_for_display


class BiomeTableDescriptor(TableDescriptor):
    """Describe columns and rows for Biome issues."""

    def get_columns(self) -> list[str]:
        """Return ordered column headers for the Biome table.

        Returns:
            list[str]: Column names for the formatted table.
        """
        return ["File", "Line", "Column", "Code", "Severity", "Message"]

    def get_rows(
        self,
        issues: list[BiomeIssue],
    ) -> list[list[str]]:
        """Return rows for the Biome issues table.

        Args:
            issues: Parsed Biome issues to render.

        Returns:
            list[list[str]]: Table rows with normalized file path and fields.
        """
        rows = []
        for issue in issues:
            rows.append(
                [
                    normalize_file_path_for_display(issue.file),
                    str(issue.line),
                    str(issue.column),
                    issue.code,
                    issue.severity,
                    issue.message,
                ],
            )
        return rows


def format_biome_issues(
    issues: list[BiomeIssue],
    format: OutputFormat = OutputFormat.GRID,
) -> str:
    """Format Biome issues with auto-fixable labeling.

    Args:
        issues: List of BiomeIssue objects.
        format: Output format identifier (e.g., "grid", "json").

    Returns:
        str: Formatted output string.

    Notes:
        Biome issues can be auto-fixable if the fixable flag is True.
        For non-JSON formats, issues are split into auto-fixable and
        not auto-fixable sections.
        JSON returns the combined table for compatibility.
    """
    descriptor = BiomeTableDescriptor()
    formatter = get_style(format)

    if format == OutputFormat.JSON:
        columns = descriptor.get_columns()
        rows = descriptor.get_rows(issues)
        return formatter.format(columns=columns, rows=rows, tool_name="biome")

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
