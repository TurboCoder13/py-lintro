"""Issue model for rustfmt output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from lintro.parsers.base_issue import BaseIssue


@dataclass
class RustfmtIssue(BaseIssue):
    """Represents a rustfmt formatting issue.

    Rustfmt reports files that need formatting. Each issue represents
    a file that would be reformatted.

    Attributes:
        fixable: Whether the issue can be auto-fixed (always True for rustfmt).
    """

    DISPLAY_FIELD_MAP: ClassVar[dict[str, str]] = {
        **BaseIssue.DISPLAY_FIELD_MAP,
    }

    fixable: bool = field(default=True)
