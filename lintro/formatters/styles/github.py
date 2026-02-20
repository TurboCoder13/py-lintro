"""GitHub Actions workflow-command output style.

Emits ``::error``, ``::warning``, and ``::notice`` annotations that GitHub
Actions surfaces inline on pull-request diffs.

Reference: https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/workflow-commands-for-github-actions#setting-a-warning-message
"""

from __future__ import annotations

import contextlib
from typing import Any

from lintro.enums.severity_level import SeverityLevel, normalize_severity_level
from lintro.formatters.core.format_registry import OutputStyle

_SEVERITY_TO_COMMAND: dict[SeverityLevel, str] = {
    SeverityLevel.ERROR: "error",
    SeverityLevel.WARNING: "warning",
    SeverityLevel.INFO: "notice",
}


def _escape(value: str) -> str:
    """Escape special characters for GitHub Actions workflow commands.

    Args:
        value: Raw string to escape.

    Returns:
        Escaped string safe for workflow command messages.
    """
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _cell(
    name: str,
    col_index: dict[str, int],
    row: list[Any],
) -> str:
    """Extract a cell value from a row by column name.

    Args:
        name: Lowercase column name to look up.
        col_index: Mapping of column names to indices.
        row: The current row of values.

    Returns:
        Cell value as string, or empty string if not found.
    """
    idx = col_index.get(name)
    if idx is None or idx >= len(row):
        return ""
    return str(row[idx]) if row[idx] else ""


class GitHubStyle(OutputStyle):
    """Output style that emits GitHub Actions annotation commands."""

    def format(
        self,
        columns: list[str],
        rows: list[list[Any]],
        tool_name: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Format rows as GitHub Actions annotation commands.

        Args:
            columns: List of column header names.
            rows: List of row values (each row is a list of cell values).
            tool_name: Name of the tool that generated the data.
            **kwargs: Extra options (ignored).

        Returns:
            One annotation command per line.
        """
        if not rows:
            return ""

        # Build a case-insensitive column-name → index map
        col_index: dict[str, int] = {
            col.lower().replace(" ", "_"): i for i, col in enumerate(columns)
        }

        lines: list[str] = []
        for row in rows:
            file_val = _cell("file", col_index, row)
            line_val = _cell("line", col_index, row)
            col_val = _cell("column", col_index, row)
            code_val = _cell("code", col_index, row)
            severity_val = _cell("severity", col_index, row)
            message_val = _cell("message", col_index, row)

            # Resolve severity → GitHub command level
            level = "warning"  # default
            if severity_val:
                with contextlib.suppress(ValueError, KeyError):
                    level = _SEVERITY_TO_COMMAND[normalize_severity_level(severity_val)]

            # Build the properties portion
            props: list[str] = []
            if file_val:
                props.append(f"file={file_val}")
            if line_val and line_val != "-":
                props.append(f"line={line_val}")
            if col_val and col_val != "-":
                props.append(f"col={col_val}")

            # Title: "tool(CODE)" or just "tool"
            title_parts: list[str] = []
            if tool_name:
                title_parts.append(tool_name)
            if code_val:
                if title_parts:
                    title_parts[-1] += f"({code_val})"
                else:
                    title_parts.append(code_val)
            if title_parts:
                props.append(f"title={title_parts[0]}")

            props_str = ",".join(props)
            escaped_msg = _escape(message_val)

            lines.append(f"::{level} {props_str}::{escaped_msg}")

        return "\n".join(lines)
