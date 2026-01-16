"""Semgrep issue model for security and code quality findings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from lintro.parsers.base_issue import BaseIssue


@dataclass
class SemgrepIssue(BaseIssue):
    """Represents an issue found by Semgrep.

    Attributes:
        check_id: Rule ID that triggered this issue.
        end_line: Ending line number of the issue.
        end_column: Ending column number of the issue.
        severity: Severity level (ERROR, WARNING, INFO).
        category: Category of the issue (security, correctness, performance, etc.).
        cwe: List of CWE IDs associated with this issue.
        metadata: Additional metadata from the rule.
    """

    DISPLAY_FIELD_MAP: ClassVar[dict[str, str]] = {
        **BaseIssue.DISPLAY_FIELD_MAP,
        "code": "check_id",
        "severity": "severity",
    }

    check_id: str = field(default="")
    end_line: int = field(default=0)
    end_column: int = field(default=0)
    severity: str = field(default="WARNING")
    category: str = field(default="")
    cwe: list[str] | None = field(default=None)
    metadata: dict[str, object] | None = field(default=None)

    def __post_init__(self) -> None:
        """Initialize the inherited fields."""
        # Set the message field if not already set
        if not self.message:
            self.message = self._get_message()

    def _get_message(self) -> str:
        """Get the formatted issue message.

        Returns:
            Formatted issue message including check_id and severity.
        """
        parts: list[str] = []
        if self.check_id:
            parts.append(f"[{self.check_id}]")
        if self.severity:
            parts.append(f"{self.severity}:")
        if self.message:
            parts.append(self.message)
        return " ".join(parts) if parts else ""
