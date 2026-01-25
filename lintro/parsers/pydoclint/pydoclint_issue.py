"""Pydoclint issue model.

This module defines the dataclass for representing issues found by pydoclint,
a docstring linter that validates docstrings match function signatures.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class PydoclintIssue(BaseIssue):
    """Represents an issue found by pydoclint.

    Pydoclint outputs issues in the following format:
    path/file.py:line:col: DOCxxx: message

    Attributes:
        code: DOC code string (e.g., "DOC101").
    """

    code: str = field(default="")
