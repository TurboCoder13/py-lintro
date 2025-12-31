"""Issue model for actionlint output."""

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class ActionlintIssue(BaseIssue):
    """Represents a single actionlint issue parsed from CLI output.

    Attributes:
        level: Severity level (e.g., "error", "warning").
        code: Optional rule/code identifier, when present.
    """

    level: str = field(default="error")
    code: str | None = field(default=None)
