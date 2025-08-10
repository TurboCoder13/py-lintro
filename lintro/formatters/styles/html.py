from typing import Any

from lintro.formatters.core.output_style import OutputStyle


class HtmlStyle(OutputStyle):
    """Output format that renders data as HTML table."""

    def format(
        self,
        columns: list[str],
        rows: list[list[Any]],
    ) -> str:
        """Format a table given columns and rows as HTML.

        Args:
            columns: List of column header names.
            rows: List of row values (each row is a list of cell values).

        Returns:
            Formatted data as HTML table string.
        """
        if not rows:
            return "<p>No issues found.</p>"

        # Build the header
        header_cells = "".join(f"<th>{col}</th>" for col in columns)
        header = f"<tr>{header_cells}</tr>"

        # Build the rows
        formatted_rows = []
        for row in rows:
            # Ensure row has same number of elements as columns
            padded_row = row + [""] * (len(columns) - len(row))
            # Escape HTML characters in cell values
            escaped_cells = [
                str(cell)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                for cell in padded_row
            ]
            row_cells = "".join(f"<td>{cell}</td>" for cell in escaped_cells)
            formatted_rows.append(f"<tr>{row_cells}</tr>")

        # Combine all parts
        table_content = header + "".join(formatted_rows)
        return f"<table>{table_content}</table>"
