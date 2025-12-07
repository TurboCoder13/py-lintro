"""CSV output style implementation."""

import csv
import io
from typing import Any

from lintro.formatters.core.output_style import OutputStyle


class CsvStyle(OutputStyle):
    """Output format that renders data as CSV."""

    def format(
        self,
        columns: list[str],
        rows: list[list[Any]],
        tool_name: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Format a table given columns and rows as CSV.

        Args:
            columns: List of column header names.
            rows: List of row values (each row is a list of cell values).
            tool_name: Optional tool name to include in context.
            **kwargs: Extra options ignored by this formatter.

        Returns:
            Formatted data as CSV string.
        """
        if not rows:
            return ""

        # Create a string buffer to write CSV data
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(columns)

        # Write rows
        for row in rows:
            # Ensure row has same number of elements as columns
            padded_row = row + [""] * (len(columns) - len(row))
            writer.writerow(padded_row)

        return output.getvalue()
