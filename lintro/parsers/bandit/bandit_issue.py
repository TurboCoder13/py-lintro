"""Bandit issue model for security vulnerabilities."""

from dataclasses import dataclass, field
from typing import Any, ClassVar

from lintro.parsers.base_issue import BaseIssue


@dataclass
class BanditIssue(BaseIssue):
    """Represents a security issue found by Bandit.

    Attributes:
        col_offset: int: Column offset of the issue.
        issue_severity: str: Severity level (LOW, MEDIUM, HIGH).
        issue_confidence: str: Confidence level (LOW, MEDIUM, HIGH).
        test_id: str: Bandit test ID (e.g., B602, B301).
        test_name: str: Name of the test that found the issue.
        issue_text: str: Description of the security issue.
        more_info: str: URL with more information about the issue.
        cwe: dict[str, Any] | None: CWE (Common Weakness Enumeration) information.
        code_snippet: str: Code snippet containing the issue.
        line_range: list[int]: Range of lines containing the issue.
    """

    DISPLAY_FIELD_MAP: ClassVar[dict[str, str]] = {
        **BaseIssue.DISPLAY_FIELD_MAP,
        "code": "test_id",
        "message": "issue_text",
        "severity": "issue_severity",
    }

    col_offset: int = field(default=0)
    issue_severity: str = field(default="UNKNOWN")
    issue_confidence: str = field(default="UNKNOWN")
    test_id: str = field(default="")
    test_name: str = field(default="")
    issue_text: str = field(default="")
    more_info: str = field(default="")
    cwe: dict[str, Any] | None = field(default=None)
    code_snippet: str | None = field(default=None)
    line_range: list[int] | None = field(default=None)

    def __post_init__(self) -> None:
        """Initialize the inherited fields."""
        # Map col_offset to column for BaseIssue compatibility
        self.column = self.col_offset
        # Set the message field to the computed value for general use
        self.message = self._get_message()

    def _get_message(self) -> str:
        """Get the formatted issue message.

        Returns:
            str: Formatted issue message.
        """
        return (
            f"[{self.test_id}:{self.test_name}] {self.issue_severity} severity, "
            f"{self.issue_confidence} confidence: {self.issue_text}"
        )
