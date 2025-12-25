"""Black issue models.

This module defines lightweight dataclasses used to represent Black findings
in a normalized form that Lintro formatters can consume.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class BlackIssue(BaseIssue):
    """Represents a Black formatting issue.

    Attributes:
        fixable: Whether this issue can be auto-fixed by Black. Defaults to True
            for standard formatting issues. Set to False for line length violations
            that Black cannot safely wrap.
    """

    fixable: bool = field(default=True)
