"""Typed structure representing a single Darglint issue."""

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class DarglintIssue(BaseIssue):
    """Simple container for Darglint findings.

    Attributes:
        code: Darglint error code.
    """

    code: str = field(default="")
