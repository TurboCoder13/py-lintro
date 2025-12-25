"""Models for mypy issues."""

from __future__ import annotations

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class MypyIssue(BaseIssue):  # type: ignore[misc]
    """Represents a mypy type-checking issue.

    Attributes:
        code: Mypy error code (e.g., attr-defined, name-defined).
        severity: Severity level reported by mypy (e.g., error, note).
        end_line: Optional end line number.
        end_column: Optional end column number.
    """

    code: str | None = field(default=None)
    severity: str | None = field(default=None)
    end_line: int | None = field(default=None)
    end_column: int | None = field(default=None)
