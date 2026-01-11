"""Markdown output style implementation."""

from typing import Any

from lintro.formatters.core.format_registry import OutputStyle


class MarkdownStyle(OutputStyle):
    """Output format that renders data as markdown table."""

    def format(
        self,
        columns: list[str],
        rows: list[list[Any]],
        tool_name: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Format a table given columns and rows as markdown.

        Args:
            columns: List of column header names.
            rows: List of row values (each row is a list of cell values).
            tool_name: Optional tool name to include in context.
            **kwargs: Extra options ignored by this formatter.

        Returns:
            Formatted data as markdown table string.
        """
        if not rows:
            return "No issues found."

        # Build the header
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join("---" for _ in columns) + " |"

        # Build the rows
        formatted_rows = []
        for row in rows:
            # Ensure row has same number of elements as columns
            padded_row = row + [""] * (len(columns) - len(row))
            # Escape pipe characters in cell values
            escaped_cells = [str(cell).replace("|", "\\|") for cell in padded_row]
            formatted_rows.append("| " + " | ".join(escaped_cells) + " |")

        # Combine all parts
        result = [header, separator] + formatted_rows
        return "\n".join(result)
