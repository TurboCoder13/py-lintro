"""Model for ruff formatting issues."""

from dataclasses import dataclass, field
from typing import ClassVar

from lintro.enums.severity_level import SeverityLevel
from lintro.parsers.base_issue import BaseIssue


@dataclass
class RuffFormatIssue(BaseIssue):
    """Represents a ruff formatting issue.

    Inherits from BaseIssue to be compatible with the unified formatter.

    Attributes:
        DEFAULT_SEVERITY: Defaults to INFO (pure formatter).
        code: Defaults to "FORMAT" for format issues.
        message: Defaults to "Would reformat file" for format issues.
        fixable: Defaults to True since format issues are auto-fixable by fmt.
    """

    DEFAULT_SEVERITY: ClassVar[SeverityLevel] = SeverityLevel.INFO

    # file is inherited from BaseIssue
    code: str = field(default="FORMAT")
    message: str = field(default="Would reformat file")
    fixable: bool = field(default=True)
