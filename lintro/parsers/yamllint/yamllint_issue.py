"""Yamllint issue model."""

from dataclasses import dataclass, field

from lintro.enums.severity_level import SeverityLevel
from lintro.parsers.base_issue import BaseIssue


@dataclass
class YamllintIssue(BaseIssue):
    """Represents an issue found by yamllint.

    Attributes:
        level: Severity level (error, warning)
        rule: Rule name that was violated (e.g., line-length, trailing-spaces)
    """

    level: SeverityLevel = field(default=SeverityLevel.ERROR)
    rule: str | None = field(default=None)
