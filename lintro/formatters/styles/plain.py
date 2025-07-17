from typing import List, Any

from lintro.formatters.core.output_style import OutputStyle


class PlainStyle(OutputStyle):
    def format(
        self,
        columns: List[str],
        rows: List[List[Any]],
    ) -> str:
        if not rows:
            return "No issues found."
        # Calculate column widths
        col_widths = [
            max(len(str(col)), max((len(str(row[i])) for row in rows), default=0))
            for i, col in enumerate(columns)
        ]
        header = " ".join(f"{col:<{col_widths[i]}}" for i, col in enumerate(columns))
        sep = "-" * (sum(col_widths) + len(col_widths) - 1)
        lines = [header, sep]
        for row in rows:
            lines.append(
                " ".join(f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(row))
            )
        return "\n".join(lines)
