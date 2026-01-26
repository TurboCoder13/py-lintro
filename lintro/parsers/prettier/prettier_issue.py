"""Typed structure representing a single Prettier issue."""

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class PrettierIssue(BaseIssue):
    """Simple container for Prettier findings.

    Attributes:
        code: Tool-specific code identifying the rule.
    """

    code: str = field(default="")
