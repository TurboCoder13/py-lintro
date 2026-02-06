"""Models for vue-tsc issues."""

from __future__ import annotations

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class VueTscIssue(BaseIssue):
    """Represents a vue-tsc type checking issue.

    This class extends BaseIssue with vue-tsc-specific fields for type checking
    errors and warnings in Vue Single File Components. The output format is
    identical to tsc.

    Attributes:
        code: TypeScript error code (e.g., "TS2322", "TS1234").
            None if vue-tsc doesn't provide an error code.
        severity: Severity level reported by vue-tsc (e.g., "error", "warning").
            None if severity is not specified.

    Examples:
        >>> issue = VueTscIssue(
        ...     file="src/components/Button.vue",
        ...     line=15,
        ...     column=5,
        ...     code="TS2322",
        ...     severity="error",
        ...     message="Type 'string' is not assignable to type 'number'.",
        ... )
    """

    code: str | None = field(default=None)
    severity: str | None = field(default=None)
