"""Plain text output style implementation."""

from typing import Any

from lintro.formatters.core.output_style import OutputStyle


class PlainStyle(OutputStyle):
    """Output format that renders data as plain text."""

    def format(
        self,
        columns: list[str],
        rows: list[list[Any]],
    ) -> str:
        """Format a table given columns and rows as plain text.

        Args:
            columns: List of column header names.
            rows: List of row values (each row is a list of cell values).

        Returns:
            Formatted data as plain text string.
        """
        if not rows:
            return "No issues found."

        # Build the header
        header = " | ".join(columns)
        separator = "-" * len(header)

        # Build the rows
        formatted_rows = []
        for row in rows:
            # Ensure row has same number of elements as columns
            padded_row = row + [""] * (len(columns) - len(row))
            formatted_rows.append(" | ".join(str(cell) for cell in padded_row))

        # Combine all parts
        result = [header, separator] + formatted_rows
        return "\n".join(result)
