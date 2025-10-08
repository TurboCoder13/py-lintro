"""Typed structure representing a single Darglint issue."""

from dataclasses import dataclass


@dataclass
class DarglintIssue:
    """Simple container for Darglint findings.

    Attributes:
        file: File path where the issue occurred.
        line: Line number of the issue.
        code: Darglint error code.
        message: Human-readable description of the issue.
    """

    file: str
    line: int
    code: str
    message: str
