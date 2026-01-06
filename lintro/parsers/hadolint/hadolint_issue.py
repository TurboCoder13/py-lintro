"""Hadolint issue model."""

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class HadolintIssue(BaseIssue):
    """Represents an issue found by hadolint.

    Attributes:
        level: Severity level (error, warning, info, style)
        code: Rule code (e.g., DL3006, SC2086)
        column: Column number where the issue occurs (if available)
    """

    level: str = field(default="error")
    code: str = field(default="")
    # Note: column is inherited from BaseIssue
