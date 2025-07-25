from typing import Any, List

from lintro.formatters.core.output_style import OutputStyle


class MarkdownStyle(OutputStyle):
    def format(
        self,
        columns: List[str],
        rows: List[List[Any]],
    ) -> str:
        if not rows:
            return ""  # Let the caller handle "No issues found" display
        header = "| " + " | ".join(columns) + " |"
        sep = "|" + "|".join(["---"] * len(columns)) + "|"
        lines = [header, sep]
        for row in rows:
            lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
        return "\n".join(lines)
