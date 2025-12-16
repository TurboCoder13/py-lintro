"""Models for Clippy issues."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ClippyIssue:
    """Represents a Clippy linting issue.

    Attributes:
        file: File path where the issue was found.
        line: Line number for the issue start.
        column: Column number for the issue start.
        code: Clippy lint code (e.g., clippy::needless_return).
        message: Human-readable error message.
        level: Severity level (e.g., warning, error).
        end_line: Optional end line number.
        end_column: Optional end column number.
    """

    file: str
    line: int
    column: int
    code: str | None
    message: str
    level: str | None = None
    end_line: int | None = None
    end_column: int | None = None
