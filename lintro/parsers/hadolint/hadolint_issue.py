"""Hadolint issue model."""

from dataclasses import dataclass


@dataclass
class HadolintIssue:
    """Represents an issue found by hadolint.

    Attributes:
        file: File path where the issue was found
        line: Line number where the issue occurs
        column: Column number where the issue occurs (if available)
        level: Severity level (error, warning, info, style)
        code: Rule code (e.g., DL3006, SC2086)
        message: Description of the issue
    """

    file: str
    line: int
    column: int | None
    level: str
    code: str
    message: str
