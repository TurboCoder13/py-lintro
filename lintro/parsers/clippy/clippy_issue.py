"""Models for Clippy issues."""

from __future__ import annotations

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class ClippyIssue(BaseIssue):
    """Represents a Clippy linting issue.

    Attributes:
        code: Clippy lint code (e.g., clippy::needless_return).
        level: Severity level (e.g., warning, error).
        end_line: Optional end line number.
        end_column: Optional end column number.
    """

    code: str | None = field(default=None)
    level: str | None = field(default=None)
    end_line: int | None = field(default=None)
    end_column: int | None = field(default=None)
