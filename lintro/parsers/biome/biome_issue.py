"""Typed structure representing a single Biome diagnostic."""

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class BiomeIssue(BaseIssue):
    """Simple container for Biome findings.

    Attributes:
        end_line: End line number (optional, 1-based).
        end_column: End column number (optional, 1-based).
        code: Rule category (e.g., 'lint/suspicious/noDoubleEquals').
        severity: Severity level ('error', 'warning', 'info').
        fixable: Whether this issue can be auto-fixed.
    """

    end_line: int | None = field(default=None)
    end_column: int | None = field(default=None)
    code: str = field(default="")
    severity: str = field(default="error")
    fixable: bool = field(default=False)
