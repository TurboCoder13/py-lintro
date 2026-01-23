"""Typed structure representing a single Oxlint diagnostic."""

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class OxlintIssue(BaseIssue):
    """Simple container for Oxlint findings.

    Attributes:
        code: Rule code (e.g., 'eslint(no-unused-vars)').
        severity: Severity level ('error', 'warning').
        fixable: Whether this issue can be auto-fixed.
        help: Optional help text with suggested fix.
    """

    code: str = field(default="")
    severity: str = field(default="warning")
    fixable: bool = field(default=False)
    help: str | None = field(default=None)
