"""Core model for tool configuration used by Lintro tools."""

from dataclasses import dataclass, field

from lintro.enums.tool_type import ToolType


@dataclass
class ToolConfig:
    """Configuration container for a tool.

    This dataclass defines the static configuration associated with a tool,
    including its priority, file targeting, type flags, and default options.

    Attributes:
        priority: int: Priority used when ordering tools.
        conflicts_with: list[str]: Names of tools that conflict with this one.
        file_patterns: list[str]: Glob patterns to select applicable files.
        tool_type: ToolType: Bitmask describing tool capabilities.
        options: dict[str, object]: Default tool options applied at runtime.
    """

    priority: int = 0
    conflicts_with: list[str] = field(default_factory=list)
    file_patterns: list[str] = field(default_factory=list)
    tool_type: ToolType = ToolType.LINTER
    options: dict[str, object] = field(default_factory=dict)
