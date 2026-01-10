"""Markdownlint issue model."""

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class MarkdownlintIssue(BaseIssue):
    """Represents an issue found by markdownlint-cli2.

    Attributes:
        code: Rule code that was violated (e.g., MD013, MD041)
        column: Column number where the issue occurs (if available)
    """

    code: str = field(default="")
