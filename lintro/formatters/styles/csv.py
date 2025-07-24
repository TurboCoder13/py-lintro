import csv
import io
from typing import Any, List

from lintro.formatters.core.output_style import OutputStyle


class CsvStyle(OutputStyle):
    """Output format that renders data as CSV."""

    def format(
        self,
        columns: List[str],
        rows: List[List[Any]],
    ) -> str:
        """Format a table given columns and rows as CSV.

        Args:
            columns: List of column names.
            rows: List of row values (each row is a list of cell values).

        Returns:
            Formatted data as CSV string.
        """
        if not rows:
            return ""

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(columns)

        # Write data rows
        for row in rows:
            writer.writerow([str(cell) for cell in row])

        return output.getvalue().strip()
