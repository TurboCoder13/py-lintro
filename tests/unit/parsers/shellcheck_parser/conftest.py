"""Shared fixtures and utilities for shellcheck parser tests."""

from __future__ import annotations

import json
from typing import Any


def make_shellcheck_output(issues: list[dict[str, Any]]) -> str:
    """Create JSON output string from a list of issue dictionaries.

    Args:
        issues: List of issue dictionaries to serialize.

    Returns:
        JSON string representation of the issues.
    """
    return json.dumps(issues)


def make_issue(
    *,
    file: str = "script.sh",
    line: int = 10,
    column: int = 5,
    level: str = "warning",
    code: int | str = 2086,
    message: str = "Test message",
    end_line: int | None = None,
    end_column: int | None = None,
) -> dict[str, Any]:
    """Create a shellcheck issue dictionary with sensible defaults.

    Args:
        file: The file path.
        line: The line number.
        column: The column number.
        level: The severity level.
        code: The error code.
        message: The error message.
        end_line: Optional end line number.
        end_column: Optional end column number.

    Returns:
        Dictionary representing a shellcheck issue.
    """
    issue: dict[str, Any] = {
        "file": file,
        "line": line,
        "column": column,
        "level": level,
        "code": code,
        "message": message,
    }
    if end_line is not None:
        issue["endLine"] = end_line
    if end_column is not None:
        issue["endColumn"] = end_column
    return issue
