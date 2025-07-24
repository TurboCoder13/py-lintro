from typing import Any, List

from lintro.formatters.core.output_style import OutputStyle


class HtmlStyle(OutputStyle):
    """Output format that renders tables as HTML."""

    def format(
        self,
        columns: List[str],
        rows: List[List[Any]],
    ) -> str:
        """Format a table given columns and rows as HTML.

        Args:
            columns: List of column names.
            rows: List of row values (each row is a list of cell values).

        Returns:
            Formatted table as HTML string, or empty string if no rows.
        """
        if not rows:
            return ""  # Let the caller handle "No issues found" display

        html_lines = ["<table>"]

        # Header row
        html_lines.append("  <thead>")
        html_lines.append("    <tr>")
        for col in columns:
            html_lines.append(f"      <th>{self._escape_html(str(col))}</th>")
        html_lines.append("    </tr>")
        html_lines.append("  </thead>")

        # Body rows
        html_lines.append("  <tbody>")
        for row in rows:
            html_lines.append("    <tr>")
            for cell in row:
                html_lines.append(f"      <td>{self._escape_html(str(cell))}</td>")
            html_lines.append("    </tr>")
        html_lines.append("  </tbody>")
        html_lines.append("</table>")

        return "\n".join(html_lines)

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters.

        Args:
            text: Input text to escape HTML characters from.

        Returns:
            str: Text with HTML special characters escaped.
        """
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )
