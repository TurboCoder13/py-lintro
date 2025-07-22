"""Models for core results."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolResult:
    """Result of running a core.

    Attributes:
        name: Name of the core.
        success: Whether the core ran successfully.
        output: Output from the core (str | None if no output).
        issues_count: Number of issues found by the core.
        formatted_output: Formatted output for display (e.g., JSON, HTML).
    """

    name: str
    success: bool
    output: str | None = None
    issues_count: int = 0
    formatted_output: Optional[str] = None
