"""Typed structure representing a single ESLint issue."""

from dataclasses import dataclass


@dataclass
class EslintIssue:
    """Simple container for ESLint findings.

    Attributes:
        file: File path where the issue occurred.
        line: Line number where the issue occurred.
        column: Column number where the issue occurred.
        code: Rule ID that triggered the issue (e.g., 'no-unused-vars').
        message: Human-readable description of the issue.
        severity: Severity level (1=warning, 2=error).
        fixable: Whether this issue can be auto-fixed.
    """

    file: str
    line: int
    column: int
    code: str
    message: str
    severity: int
    fixable: bool = False
