"""Shfmt issue model.

This module defines a lightweight dataclass used to represent shfmt findings
in a normalized form that Lintro formatters can consume.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class ShfmtIssue(BaseIssue):
    """Represents a shfmt formatting issue.

    Shfmt detects shell script formatting issues and outputs them in diff
    format. This class captures the file and line information along with
    the diff content showing what needs to be changed.

    Attributes:
        diff_content: The diff content showing the formatting change needed.
            Empty string if not available (e.g., when only file-level info
            is reported).
        fixable: Whether this issue can be auto-fixed by shfmt. Defaults to
            True since shfmt can fix all formatting issues it detects.
    """

    diff_content: str = field(default="")
    fixable: bool = field(default=True)
