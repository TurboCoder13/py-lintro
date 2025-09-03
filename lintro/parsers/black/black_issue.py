"""Black issue models.

This module defines lightweight dataclasses used to represent Black findings
in a normalized form that Lintro formatters can consume.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BlackIssue:
    """Represents a Black formatting issue.

    Attributes:
        file: Path to the file with a formatting difference.
        message: Short human-readable description (e.g., "Would reformat file").
    """

    file: str
    message: str
