"""Models for pytest issues."""

from dataclasses import dataclass


@dataclass
class PytestIssue:
    """Represents a pytest test failure or error.

    Attributes:
        file: File path where the test failure occurred.
        line: Line number where the failure occurred.
        test_name: Name of the failing test.
        message: Error message or failure description.
        test_status: Status of the test (FAILED, ERROR, etc.).
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
