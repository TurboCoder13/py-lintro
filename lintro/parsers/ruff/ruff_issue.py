"""Models for ruff issues."""

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class RuffIssue(BaseIssue):
    """Represents a ruff linting issue.

    Attributes:
        code: Ruff error code (e.g., E401, F401).
        url: Optional URL to documentation for this error.
        end_line: End line number for multi-line issues.
        end_column: End column number for multi-line issues.
        fixable: Whether this issue can be auto-fixed.
        fix_applicability: Whether the fix is safe or unsafe (safe, unsafe, or None).
    """

    code: str = field(default="")
    url: str | None = field(default=None)
    end_line: int | None = field(default=None)
    end_column: int | None = field(default=None)
    fixable: bool = field(default=False)
    fix_applicability: str | None = field(default=None)


@dataclass
class RuffFormatIssue:
    """Represents a ruff formatting issue.

    Attributes:
        file: File path that would be reformatted.
    """

    file: str
