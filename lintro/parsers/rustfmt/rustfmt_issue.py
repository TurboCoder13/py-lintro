"""Issue model for rustfmt output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from lintro.enums.severity_level import SeverityLevel
from lintro.parsers.base_issue import BaseIssue


@dataclass
class RustfmtIssue(BaseIssue):
    """Represents a rustfmt formatting issue.

    Rustfmt reports files that need formatting. Each issue represents
    a file that would be reformatted.

    Attributes:
        DISPLAY_FIELD_MAP: Mapping of display field names to attribute names.
        DEFAULT_SEVERITY: Defaults to INFO (pure formatter).
        fixable: Whether the issue can be auto-fixed (always True for rustfmt).
    """

    DISPLAY_FIELD_MAP: ClassVar[dict[str, str]] = {
        **BaseIssue.DISPLAY_FIELD_MAP,
    }

    DEFAULT_SEVERITY: ClassVar[SeverityLevel] = SeverityLevel.INFO

    fixable: bool = field(default=True)
