"""Typed structure representing a single oxfmt issue."""

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class OxfmtIssue(BaseIssue):
    """Simple container for oxfmt findings.

    Attributes:
        code: Tool-specific code identifying the rule (default: FORMAT).
    """

    code: str = field(default="FORMAT")
