"""Models for core tool execution results.

This module defines the canonical result object returned by all tools. It
supports both check and fix flows and includes standardized fields to report
fixed vs remaining counts for fix-capable tools.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field


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

    name: str = field(default="")
    success: bool = field(default=False)
    output: str | None = field(default=None)
    issues_count: int = field(default=0)
    formatted_output: str | None = field(default=None)
    issues: Sequence[object] | None = field(default=None)

    # Optional standardized counts for fix-capable tools
    initial_issues_count: int | None = field(default=None)
    fixed_issues_count: int | None = field(default=None)
    remaining_issues_count: int | None = field(default=None)

    def __post_init__(self) -> None:
        """Validate that the issue counts are consistent.

        Raises:
            ValueError: If issue counts are inconsistent.
        """
        if (
            self.initial_issues_count is not None
            and self.fixed_issues_count is not None
            and self.remaining_issues_count is not None
            and self.initial_issues_count
            != self.fixed_issues_count + self.remaining_issues_count
        ):
            raise ValueError(
                f"Inconsistent issue counts: "
                f"initial={self.initial_issues_count}, "
                f"fixed={self.fixed_issues_count}, "
                f"remaining={self.remaining_issues_count}. "
                f"Expected: initial = fixed + remaining",
            )
