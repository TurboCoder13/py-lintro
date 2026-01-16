"""Gitleaks issue model for secret detection findings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from lintro.parsers.base_issue import BaseIssue


@dataclass
class GitleaksIssue(BaseIssue):
    """Represents a secret detection finding from Gitleaks.

    Attributes:
        rule_id: The rule ID that triggered the detection (e.g., aws-access-key-id).
        description: Description of the secret type detected.
        secret: The detected secret value (should be redacted for display).
        entropy: Shannon entropy of the detected secret.
        tags: List of tags associated with the rule.
        fingerprint: Unique identifier for this finding.
        end_line: End line number of the finding.
        end_column: End column number of the finding.
        match: The matched pattern string.
        commit: Git commit hash if scanning git history.
        author: Git author if scanning git history.
        email: Git author email if scanning git history.
        date: Git commit date if scanning git history.
        commit_message: Git commit message if scanning git history.
    """

    DISPLAY_FIELD_MAP: ClassVar[dict[str, str]] = {
        **BaseIssue.DISPLAY_FIELD_MAP,
        "code": "rule_id",
        # message uses the computed value from __post_init__ (default mapping)
    }

    rule_id: str = field(default="")
    description: str = field(default="")
    secret: str = field(default="")
    entropy: float = field(default=0.0)
    tags: list[str] = field(default_factory=list)
    fingerprint: str = field(default="")
    end_line: int = field(default=0)
    end_column: int = field(default=0)
    match: str = field(default="")
    commit: str = field(default="")
    author: str = field(default="")
    email: str = field(default="")
    date: str = field(default="")
    commit_message: str = field(default="")

    def __post_init__(self) -> None:
        """Initialize the inherited message field."""
        self.message = self._get_message()

    def _get_message(self) -> str:
        """Get the formatted issue message.

        Returns:
            Formatted issue message with redacted secret.
        """
        redacted_hint = "[REDACTED]" if self.secret else ""
        return f"[{self.rule_id}] {self.description} {redacted_hint}".strip()
