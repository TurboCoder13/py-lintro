"""Models for mypy issues."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MypyIssue:
    """Represents a mypy type-checking issue.

    Attributes:
        file: File path where the issue was found.
        line: Line number for the issue start.
        column: Column number for the issue start.
        code: Mypy error code (e.g., attr-defined, name-defined).
        message: Human-readable error message.
        severity: Severity level reported by mypy (e.g., error, note).
        end_line: Optional end line number.
        end_column: Optional end column number.
    """

    file: str
    line: int
    column: int
    code: str | None
    message: str
    severity: str | None = None
    end_line: int | None = None
    end_column: int | None = None
