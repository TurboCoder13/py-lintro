"""Typed structure representing a single Prettier issue."""

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class PrettierIssue(BaseIssue):
    """Simple container for Prettier findings.

    Attributes:
        code: Tool-specific code identifying the rule.
        line: Line number, if provided by Prettier.
        column: Column number, if provided by Prettier.
    """

    code: str = field(default="")
    # Note: line and column are inherited from BaseIssue
