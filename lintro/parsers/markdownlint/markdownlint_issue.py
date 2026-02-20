"""Markdownlint issue model."""

from dataclasses import dataclass, field
from typing import ClassVar

from lintro.enums.severity_level import SeverityLevel
from lintro.parsers.base_issue import BaseIssue


@dataclass
class MarkdownlintIssue(BaseIssue):
    """Represents an issue found by markdownlint-cli2.

    Attributes:
        DEFAULT_SEVERITY: Defaults to INFO (style/formatting tool).
        code: Rule code that was violated (e.g., MD013, MD041).
    """

    DEFAULT_SEVERITY: ClassVar[SeverityLevel] = SeverityLevel.INFO

    code: str = field(default="")
