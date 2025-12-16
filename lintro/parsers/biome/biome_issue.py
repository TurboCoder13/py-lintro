"""Typed structure representing a single Biome diagnostic."""

from dataclasses import dataclass


@dataclass
class BiomeIssue:
    """Simple container for Biome findings.

    Attributes:
        file: File path where the issue occurred.
        line: Line number where the issue occurred (1-based).
        column: Column number where the issue occurred (1-based).
        end_line: End line number (optional, 1-based).
        end_column: End column number (optional, 1-based).
        code: Rule category (e.g., 'lint/suspicious/noDoubleEquals').
        message: Human-readable description of the issue.
        severity: Severity level ('error', 'warning', 'info').
        fixable: Whether this issue can be auto-fixed.
    """

    file: str
    line: int
    column: int
    end_line: int | None = None
    end_column: int | None = None
    code: str = ""
    message: str = ""
    severity: str = "error"
    fixable: bool = False
