"""Typed structure representing a single Prettier issue."""

from dataclasses import dataclass


@dataclass
class PrettierIssue:
    """Simple container for Prettier findings.

    Attributes:
        file: File path where the issue occurred.
        line: Line number, if provided by Prettier.
        code: Tool-specific code identifying the rule.
        message: Human-readable description of the issue.
        column: Column number, if provided by Prettier.
    """

    file: str
    line: int | None
    code: str
    message: str
    column: int | None = None
