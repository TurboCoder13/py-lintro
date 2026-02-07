"""Models for astro check issues."""

from __future__ import annotations

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class AstroCheckIssue(BaseIssue):
    """Represents an Astro check diagnostic issue.

    This class extends BaseIssue with astro-check-specific fields for type
    checking errors and warnings in Astro components.

    Attributes:
        code: TypeScript error code (e.g., "TS2322", "TS1234").
            Empty string if astro check doesn't provide an error code.
        severity: Severity level reported by astro check (e.g., "error", "warning").
            None if severity is not specified.
        hint: Optional hint text providing additional context.
            None if no hint is provided.

    Examples:
        >>> issue = AstroCheckIssue(
        ...     file="src/pages/index.astro",
        ...     line=10,
        ...     column=5,
        ...     code="TS2322",
        ...     severity="error",
        ...     message="Type 'string' is not assignable to type 'number'.",
        ... )
    """

    code: str = field(default="")
    severity: str | None = field(default=None)
    hint: str | None = field(default=None)
