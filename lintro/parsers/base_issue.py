"""Base issue class for all linting tool issues.

This module provides a common base class for all issue types to reduce
duplication across the 14+ different issue dataclasses.

The base class includes:
- Common fields (file, line, column, message)
- A to_display_row() method for unified formatting with configurable field mapping
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class BaseIssue:
    """Base class for all linting issues with unified display support.

    Provides common fields that are shared across all issue types.
    Specific issue types should inherit from this class and add their
    own fields as needed.

    The to_display_row() method converts the issue to a dictionary format
    suitable for the unified formatter. Subclasses can customize the mapping
    by setting DISPLAY_FIELD_MAP class variable instead of overriding the method.

    Class Variables:
        DISPLAY_FIELD_MAP: Maps display keys to attribute names for custom fields.
            Default mappings: code→code, severity→severity, fixable→fixable.
            Example: {"severity": "level"} to map self.level to severity output.

    Attributes:
        file: File path where the issue was found.
        line: Line number where the issue was found (1-based, 0 means unknown).
        column: Column number where the issue was found (1-based, 0 means unknown).
        message: Human-readable description of the issue.
    """

    # Default field mapping - subclasses can override specific keys
    DISPLAY_FIELD_MAP: ClassVar[dict[str, str]] = {
        "code": "code",
        "severity": "severity",
        "fixable": "fixable",
        "message": "message",
    }

    file: str = field(default="")
    line: int = field(default=0)
    column: int = field(default=0)
    message: str = field(default="")

    def to_display_row(self) -> dict[str, str]:
        """Convert issue to unified display format.

        Returns a dictionary with standardized keys that the unified formatter
        can use to create consistent output across all tools.

        Uses DISPLAY_FIELD_MAP to resolve attribute names, allowing subclasses
        to customize field mapping without overriding this method.

        Returns:
            Dictionary with keys: file, line, column, code, message, severity, fixable.
        """
        # Get the field mapping (supports inheritance)
        field_map = self.DISPLAY_FIELD_MAP

        # Resolve each mapped field
        code_attr = field_map.get("code", "code")
        severity_attr = field_map.get("severity", "severity")
        fixable_attr = field_map.get("fixable", "fixable")
        message_attr = field_map.get("message", "message")

        code_val = getattr(self, code_attr, None) or ""
        severity_val = getattr(self, severity_attr, None) or ""
        fixable_val = getattr(self, fixable_attr, False)
        message_val = getattr(self, message_attr, "") or ""

        return {
            "file": self.file,
            "line": str(self.line) if self.line else "-",
            "column": str(self.column) if self.column else "-",
            "code": str(code_val) if code_val else "",
            "message": message_val,
            "severity": str(severity_val) if severity_val else "",
            "fixable": "Yes" if fixable_val else "",
        }
