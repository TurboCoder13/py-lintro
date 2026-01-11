"""Model for ruff formatting issues."""

from dataclasses import dataclass

from lintro.parsers.base_issue import BaseIssue


@dataclass
class RuffFormatIssue(BaseIssue):
    """Represents a ruff formatting issue.

    Inherits from BaseIssue to be compatible with the unified formatter.

    Attributes:
        file: File path that would be reformatted.
    """

    # file is inherited from BaseIssue
