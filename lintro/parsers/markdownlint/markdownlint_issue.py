"""Markdownlint issue model."""

from dataclasses import dataclass


@dataclass
class MarkdownlintIssue:
    """Represents an issue found by markdownlint-cli2.

    Attributes:
        file: File path where the issue was found
        line: Line number where the issue occurs
        code: Rule code that was violated (e.g., MD013, MD041)
        message: Description of the issue
        column: Column number where the issue occurs (if available)
    """

    file: str
    line: int
    code: str
    message: str
    column: int | None = None
