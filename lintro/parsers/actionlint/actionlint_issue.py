"""Issue model for actionlint output."""

from dataclasses import dataclass, field
from typing import ClassVar

from lintro.parsers.base_issue import BaseIssue


@dataclass
class ActionlintIssue(BaseIssue):
    """Represents a single actionlint issue parsed from CLI output.

    Attributes:
        level: Severity level (e.g., "error", "warning").
        code: Optional rule/code identifier, when present.
    """

    DISPLAY_FIELD_MAP: ClassVar[dict[str, str]] = {
        **BaseIssue.DISPLAY_FIELD_MAP,
        "severity": "level",
    }

    level: str = field(default="error")
    code: str | None = field(default=None)
