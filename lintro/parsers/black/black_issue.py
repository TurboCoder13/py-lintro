"""Black issue models.

This module defines lightweight dataclasses used to represent Black findings
in a normalized form that Lintro formatters can consume.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from lintro.enums.severity_level import SeverityLevel
from lintro.parsers.base_issue import BaseIssue


@dataclass
class BlackIssue(BaseIssue):
    """Represents a Black formatting issue.

    Attributes:
        DEFAULT_SEVERITY: Defaults to INFO (pure formatter).
        code: Error code (e.g., "E501" for line length violations, empty for
            general formatting issues).
        severity: Severity level (e.g., "error", "warning", empty for general
            formatting issues).
        fixable: Whether this issue can be auto-fixed by Black. Defaults to True
            for standard formatting issues. Set to False for line length violations
            that Black cannot safely wrap.
    """

    DEFAULT_SEVERITY: ClassVar[SeverityLevel] = SeverityLevel.INFO

    code: str = field(default="")
    severity: str = field(default="")
    fixable: bool = field(default=True)
