"""Shellcheck issue model.

This module defines the dataclass for representing issues found by ShellCheck,
a static analysis tool for shell scripts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from lintro.parsers.base_issue import BaseIssue


@dataclass
class ShellcheckIssue(BaseIssue):
    """Represents an issue found by shellcheck.

    ShellCheck outputs issues in JSON format with the following structure:
    - file: Path to the file with the issue
    - line: Line number where the issue starts
    - column: Column number where the issue starts
    - endLine: Line number where the issue ends (optional)
    - endColumn: Column number where the issue ends (optional)
    - level: Severity level (error, warning, info, style)
    - code: SC code number (e.g., 2086)
    - message: Human-readable description of the issue

    Attributes:
        DISPLAY_FIELD_MAP: Mapping of display field names to attribute names.
        level: Severity level (error, warning, info, style).
        code: SC code number as string (e.g., "SC2086").
        end_line: Line number where the issue ends (0 if not available).
        end_column: Column number where the issue ends (0 if not available).
    """

    DISPLAY_FIELD_MAP: ClassVar[dict[str, str]] = {
        **BaseIssue.DISPLAY_FIELD_MAP,
        "severity": "level",
    }

    level: str = field(default="error")
    code: str = field(default="")
    end_line: int = field(default=0)
    end_column: int = field(default=0)
