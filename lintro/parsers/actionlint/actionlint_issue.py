"""Issue model for actionlint output."""

from dataclasses import dataclass


@dataclass
class ActionlintIssue:
    """Represents a single actionlint issue parsed from CLI output.

    Attributes:
        file: File path where the issue occurred.
        line: Line number of the issue (1-based).
        column: Column number of the issue (1-based).
        level: Severity level (e.g., "error", "warning").
        code: Optional rule/code identifier, when present.
        message: Human-readable message describing the issue.
    """

    file: str
    line: int
    column: int
    level: str
    code: str | None
    message: str
