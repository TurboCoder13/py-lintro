"""Hadolint issue model."""

from dataclasses import dataclass, field
from typing import ClassVar

from lintro.parsers.base_issue import BaseIssue


@dataclass
class HadolintIssue(BaseIssue):
    """Represents an issue found by hadolint.

    Attributes:
        DISPLAY_FIELD_MAP: Mapping of display field names to attribute names.
        level: Severity level (error, warning, info, style)
        code: Rule code (e.g., DL3006, SC2086)
    """

    DISPLAY_FIELD_MAP: ClassVar[dict[str, str]] = {
        **BaseIssue.DISPLAY_FIELD_MAP,
        "severity": "level",
    }

    level: str = field(default="error")
    code: str = field(default="")
