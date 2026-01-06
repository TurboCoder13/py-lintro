"""Models for pytest issues."""

from __future__ import annotations

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class PytestIssue(BaseIssue):
    """Represents a pytest test result (failure, error, or skip).

    Attributes:
        test_name: Name of the test.
        test_status: Status of the test (FAILED, ERROR, SKIPPED, etc.).
        duration: Duration of the test in seconds.
        node_id: Full node ID of the test.
    """

    test_name: str = field(default="")
    test_status: str = field(default="")
    duration: float | None = field(default=None)
    node_id: str | None = field(default=None)
