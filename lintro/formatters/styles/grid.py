from typing import List, Any

from lintro.formatters.core.output_style import OutputStyle

try:
    from tabulate import tabulate

    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False


class GridStyle(OutputStyle):
    """Output format that renders tables using grid-style borders with tabulate."""

    def format(
        self,
        columns: List[str],
        rows: List[List[Any]],
    ) -> str:
        """Format a table given columns and rows using grid-style borders.

        Args:
            columns: List of column names.
            rows: List of row values (each row is a list of cell values).

        Returns:
            Formatted table as a string with grid borders.
        """
        if not rows:
            return "No issues found."
        if TABULATE_AVAILABLE:
            return tabulate(rows, headers=columns, tablefmt="grid")
        # Fallback: simple text table
        col_widths = [
            max(len(str(col)), max((len(str(row[i])) for row in rows), default=0))
            for i, col in enumerate(columns)
        ]
        header = " | ".join(f"{col:<{col_widths[i]}}" for i, col in enumerate(columns))
        sep = "-+-".join("-" * col_widths[i] for i in range(len(columns)))
        lines = [header, sep]
        for row in rows:
            lines.append(
                " | ".join(
                    f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(row)
                )
            )
        return "\n".join(lines)
