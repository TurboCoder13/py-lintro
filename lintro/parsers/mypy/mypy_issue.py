"""Models for mypy issues."""

from __future__ import annotations

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class MypyIssue(BaseIssue):  # type: ignore[misc]
    """Represents a mypy type-checking issue.

    This class extends BaseIssue with mypy-specific fields for type checking
    errors, warnings, and notes. All fields are optional to handle cases where
    mypy doesn't provide complete location information.

    Attributes:
        code: Mypy error code (e.g., "attr-defined", "name-defined", "type-arg").
            None if mypy doesn't provide an error code.
        severity: Severity level reported by mypy (e.g., "error", "warning", "note").
            None if severity is not specified.
        end_line: Optional end line number for multi-line issues.
            None if the issue is on a single line or end position is unknown.
        end_column: Optional end column number for issues spanning multiple columns.
            None if the issue is at a single column or end position is unknown.

    Note:
        All fields are optional to handle cases where mypy doesn't provide
        complete location information. This is a breaking change from previous
        versions where some fields were required.

    Examples:
        >>> issue = MypyIssue(
        ...     file="src/main.py",
        ...     line=10,
        ...     column=5,
        ...     code="attr-defined",
        ...     severity="error",
        ...     message="Module has no attribute 'foo'"
        ... )
    """

    code: str | None = field(default=None)
    severity: str | None = field(default=None)
    end_line: int | None = field(default=None)
    end_column: int | None = field(default=None)
