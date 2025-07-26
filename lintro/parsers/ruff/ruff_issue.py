"""Models for ruff issues."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RuffIssue:
    """Represents a ruff linting issue.

    Attributes:
        file: File path where the issue was found.
        line: Line number where the issue was found.
        column: Column number where the issue was found.
        code: Ruff error code (e.g., E401, F401).
        message: Human-readable error message.
        url: Optional URL to documentation for this error.
        end_line: End line number for multi-line issues.
        end_column: End column number for multi-line issues.
        fixable: Whether this issue can be auto-fixed.
        fix_applicability: Whether the fix is safe or unsafe (safe, unsafe, or None).
    """

    file: str
    line: int
    column: int
    code: str
    message: str
    url: Optional[str] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    fixable: bool = False
    fix_applicability: Optional[str] = None


@dataclass
class RuffFormatIssue:
    """Represents a ruff formatting issue.

    Attributes:
        file: File path that would be reformatted.
    """

    file: str
