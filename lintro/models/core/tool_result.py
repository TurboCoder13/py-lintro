"""Models for core tool execution results.

This module defines the canonical result object returned by all tools. It
supports both check and fix flows and includes standardized fields to report
fixed vs remaining counts for fix-capable tools.
"""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Result of running a tool.

    For check operations:
        - ``issues_count`` represents the number of issues found.

    For fix/format operations:
        - ``initial_issues_count`` is the number of issues detected before fixes
        - ``fixed_issues_count`` is the number of issues the tool auto-fixed
        - ``remaining_issues_count`` is the number of issues still remaining
        - ``issues_count`` should mirror ``remaining_issues_count`` for
          backward compatibility in format-mode summaries

    The ``issues`` field can contain parsed issue objects (tool-specific) to
    support unified table formatting.
    """

    name: str
    success: bool
    output: str | None = None
    issues_count: int = 0
    formatted_output: str | None = None
    issues: Sequence[object] | None = None

    # Optional standardized counts for fix-capable tools
    initial_issues_count: int | None = None
    fixed_issues_count: int | None = None
    remaining_issues_count: int | None = None
