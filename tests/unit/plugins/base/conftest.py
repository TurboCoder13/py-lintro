"""Pytest configuration for base plugin unit tests."""

from __future__ import annotations

from dataclasses import dataclass, field

from lintro.models.core.tool_result import ToolResult
from lintro.plugins.base import BaseToolPlugin
from lintro.plugins.protocol import ToolDefinition


@dataclass
class NoFixPlugin(BaseToolPlugin):
    """Plugin that does not support fixing for testing purposes."""

    _definition: ToolDefinition = field(
        default_factory=lambda: ToolDefinition(
            name="no-fix",
            description="No fix support",
            file_patterns=["*.py"],
            can_fix=False,
        ),
    )

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition.

        Returns:
            The tool definition.
        """
        return self._definition

    def check(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Return a successful result.

        Args:
            paths: List of file paths to check.
            options: Dictionary of options for the check.

        Returns:
            A successful ToolResult.
        """
        return ToolResult(name="no-fix", success=True, output="", issues_count=0)
