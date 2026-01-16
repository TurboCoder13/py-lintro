"""Parser for shellcheck JSON output.

This module provides parsing functionality for ShellCheck's json1 output format.
ShellCheck is a static analysis tool for shell scripts that identifies bugs,
syntax issues, and suggests improvements.
"""

from __future__ import annotations

import json
from typing import Any

from lintro.parsers.shellcheck.shellcheck_issue import ShellcheckIssue


def parse_shellcheck_output(output: str | None) -> list[ShellcheckIssue]:
    """Parse shellcheck json1 output into a list of ShellcheckIssue objects.

    ShellCheck outputs JSON in the following format when using --format=json1:
    [
      {
        "file": "script.sh",
        "line": 10,
        "endLine": 10,
        "column": 5,
        "endColumn": 10,
        "level": "warning",
        "code": 2086,
        "message": "Double quote to prevent globbing and word splitting."
      }
    ]

    Args:
        output: The raw JSON output from shellcheck, or None.

    Returns:
        List of ShellcheckIssue objects.
    """
    issues: list[ShellcheckIssue] = []

    # Handle None or empty output
    if output is None or not output.strip():
        return issues

    try:
        data: list[dict[str, Any]] = json.loads(output)
    except json.JSONDecodeError:
        # If JSON parsing fails, return empty list
        return issues

    # Validate that data is a list
    if not isinstance(data, list):
        return issues

    for item in data:
        if not isinstance(item, dict):
            continue

        # Extract required fields with defaults
        file_path: str = str(item.get("file", ""))
        line: int = int(item.get("line", 0))
        column: int = int(item.get("column", 0))
        end_line: int = int(item.get("endLine", 0))
        end_column: int = int(item.get("endColumn", 0))
        level: str = str(item.get("level", "error"))
        code: int | str = item.get("code", 0)
        message: str = str(item.get("message", ""))

        # Format code as SC#### string
        code_str: str = f"SC{code}" if isinstance(code, int) else str(code)

        issues.append(
            ShellcheckIssue(
                file=file_path,
                line=line,
                column=column,
                end_line=end_line,
                end_column=end_column,
                level=level,
                code=code_str,
                message=message,
            ),
        )

    return issues
