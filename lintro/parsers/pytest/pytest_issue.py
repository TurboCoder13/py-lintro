"""Models for pytest issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from lintro.parsers.base_issue import BaseIssue


@dataclass
class PytestIssue(BaseIssue):
    """Represents a pytest test result (failure, error, or skip).

    Attributes:
        DISPLAY_FIELD_MAP: Mapping of display field names to attribute names.
        test_name: Name of the test.
        test_status: Status of the test (FAILED, ERROR, SKIPPED, etc.).
        duration: Duration of the test in seconds.
        node_id: Full node ID of the test.
    """

    DISPLAY_FIELD_MAP: ClassVar[dict[str, str]] = {
        **BaseIssue.DISPLAY_FIELD_MAP,
        "code": "test_name",
        "severity": "test_status",
    }

    test_name: str = field(default="")
    test_status: str = field(default="")
    duration: float | None = field(default=None)
    node_id: str | None = field(default=None)
