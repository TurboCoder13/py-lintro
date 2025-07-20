"""Yamllint issue model."""

from dataclasses import dataclass


@dataclass
class YamllintIssue:
    """Represents an issue found by yamllint.

    Attributes:
        file: File path where the issue was found
        line: Line number where the issue occurs
        column: Column number where the issue occurs (if available)
        level: Severity level (error, warning)
        rule: Rule name that was violated (e.g., line-length, trailing-spaces)
        message: Description of the issue
    """

    file: str
    line: int
    column: int | None
    level: str
    rule: str | None
    message: str
