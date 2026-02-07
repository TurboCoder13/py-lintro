"""Models for svelte-check issues."""

from __future__ import annotations

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class SvelteCheckIssue(BaseIssue):
    """Represents a svelte-check diagnostic issue.

    This class extends BaseIssue with svelte-check-specific fields for type
    checking errors, warnings, and hints in Svelte components.

    Attributes:
        code: Error code (e.g., "ts-2322", "css-unused-selector").
            Empty string if svelte-check doesn't provide an error code.
        severity: Severity level ("error", "warning", "hint").
            None if severity is not specified.
        end_line: Optional end line number for multi-line issues.
            None if the issue is on a single line.
        end_column: Optional end column number for issues spanning columns.
            None if the issue is at a single column.

    Examples:
        >>> issue = SvelteCheckIssue(
        ...     file="src/lib/Button.svelte",
        ...     line=15,
        ...     column=5,
        ...     code="ts-2322",
        ...     severity="error",
        ...     message="Type 'string' is not assignable to type 'number'.",
        ... )
    """

    code: str = field(default="")
    severity: str | None = field(default=None)
    end_line: int | None = field(default=None)
    end_column: int | None = field(default=None)
