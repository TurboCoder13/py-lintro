"""Bandit issue model for security vulnerabilities."""

from dataclasses import dataclass
from typing import Any


@dataclass
class BanditIssue:
    """Represents a security issue found by Bandit.

    Attributes:
        file: str: Path to the file containing the issue.
        line: int: Line number where the issue was found.
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

    file: str
    line: int
    col_offset: int
    issue_severity: str
    issue_confidence: str
    test_id: str
    test_name: str
    issue_text: str
    more_info: str
    cwe: dict[str, Any] | None = None
    code: str | None = None
    line_range: list[int] | None = None

    @property
    def message(self) -> str:
        """Get a human-readable message for the issue.

        Returns:
            str: Formatted issue message.
        """
        return (
            f"[{self.test_id}:{self.test_name}] {self.issue_severity} severity, "
            f"{self.issue_confidence} confidence: {self.issue_text}"
        )
