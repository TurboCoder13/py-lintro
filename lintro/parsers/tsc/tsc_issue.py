"""Models for tsc (TypeScript Compiler) issues."""

from __future__ import annotations

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class TscIssue(BaseIssue):
    """Represents a TypeScript compiler issue.

    This class extends BaseIssue with tsc-specific fields for type checking
    errors and warnings. All fields are optional to handle cases where
    tsc doesn't provide complete location information.

    Attributes:
        code: TypeScript error code (e.g., "TS2322", "TS1234").
            None if tsc doesn't provide an error code.
        severity: Severity level reported by tsc (e.g., "error", "warning").
            None if severity is not specified.
        end_line: Optional end line number for multi-line issues.
            None if the issue is on a single line or end position is unknown.
        end_column: Optional end column number for issues spanning multiple columns.
            None if the issue is at a single column or end position is unknown.

    Examples:
        >>> issue = TscIssue(
        ...     file="src/main.ts",
        ...     line=10,
        ...     column=5,
        ...     code="TS2322",
        ...     severity="error",
        ...     message="Type 'string' is not assignable to type 'number'.",
        ... )
    """

    code: str | None = field(default=None)
    severity: str | None = field(default=None)
    end_line: int | None = field(default=None)
    end_column: int | None = field(default=None)
