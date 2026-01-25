"""Shared fixtures and utilities for pydoclint parser tests."""

from __future__ import annotations


def make_pydoclint_output(issues: list[tuple[str, int, int, str, str]]) -> str:
    """Create pydoclint output string from a list of issue tuples.

    Pydoclint output format:
        /path/to/file.py
            10: DOC101: message

    Args:
        issues: List of tuples (file, line, col, code, message).
                Note: col is ignored as pydoclint doesn't report column info.

    Returns:
        Formatted pydoclint output string.
    """
    lines: list[str] = []
    current_file: str | None = None

    for file_path, line, _col, code, message in issues:
        # Add file path line if it's a new file
        if file_path != current_file:
            current_file = file_path
            lines.append(file_path)
        # Add indented issue line
        lines.append(f"    {line}: {code}: {message}")

    return "\n".join(lines)


def make_issue(
    *,
    file: str = "test.py",
    line: int = 10,
    column: int = 5,
    code: str = "DOC101",
    message: str = "Test message",
) -> tuple[str, int, int, str, str]:
    """Create a pydoclint issue tuple with sensible defaults.

    Args:
        file: The file path.
        line: The line number.
        column: The column number.
        code: The error code.
        message: The error message.

    Returns:
        Tuple representing a pydoclint issue.
    """
    return (file, line, column, code, message)
