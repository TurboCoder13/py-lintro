"""Bandit issue model for security vulnerabilities."""

from dataclasses import dataclass, field
from typing import Any

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
        code: str: Code snippet containing the issue.
        line_range: list[int]: Range of lines containing the issue.
    """

    col_offset: int = field(default=0)
    issue_severity: str = field(default="UNKNOWN")
    issue_confidence: str = field(default="UNKNOWN")
    test_id: str = field(default="")
    test_name: str = field(default="")
    issue_text: str = field(default="")
    more_info: str = field(default="")
    cwe: dict[str, Any] | None = field(default=None)
    code: str | None = field(default=None)
    line_range: list[int] | None = field(default=None)

    def __post_init__(self) -> None:
        """Initialize the inherited fields."""
        # Map col_offset to column for BaseIssue compatibility
        self.column = self.col_offset
        # Set the message using the property
        self.message = self._get_message()

    @property
    def message(self) -> str:
        """Get a human-readable message for the issue.

        Returns:
            str: Formatted issue message.
        """
        return self._get_message()

    @message.setter
    def message(self, value: str) -> None:
        """Allow setting message (for BaseIssue compatibility).

        Args:
            value: The message value to set (ignored).
        """
        # We compute message dynamically, so we ignore setting it
        pass

    def _get_message(self) -> str:
        """Get the formatted issue message.

        Returns:
            str: Formatted issue message.
        """
        return (
            f"[{self.test_id}:{self.test_name}] {self.issue_severity} severity, "
            f"{self.issue_confidence} confidence: {self.issue_text}"
        )
