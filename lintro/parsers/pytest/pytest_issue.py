"""Models for pytest issues."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PytestIssue:
    """Represents a pytest test result (failure, error, or skip).

    Attributes:
        file: File path where the test issue occurred.
        line: Line number where the issue occurred.
        test_name: Name of the test.
        message: Error message, failure description, or skip reason.
        test_status: Status of the test (FAILED, ERROR, SKIPPED, etc.).
        duration: Duration of the test in seconds.
        node_id: Full node ID of the test.
    """

    file: str
    line: int
    test_name: str
    message: str
    test_status: str
    duration: float | None = None
    node_id: str | None = None
