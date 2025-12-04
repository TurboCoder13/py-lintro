"""Markdownlint issue model."""

from dataclasses import dataclass


@dataclass
class MarkdownlintIssue:
    """Represents an issue found by markdownlint-cli2.

    Attributes:
        file: File path where the issue was found
        line: Line number where the issue occurs
        column: Column number where the issue occurs (if available)
        code: Rule code that was violated (e.g., MD013, MD041)
        message: Description of the issue
    """

    file: str
    line: int
    column: int | None
    code: str
    message: str
