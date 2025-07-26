from dataclasses import dataclass, field
from typing import Any

from lintro.enums.tool_type import ToolType


@dataclass
class ToolConfig:
    """Configuration for a core.

    Attributes:
        priority: Priority level (higher number = higher priority when resolving
            conflicts)
        conflicts_with: List of tools this core conflicts with
        file_patterns: List of file patterns this core should be applied to
        tool_type: Type of core
        options: Tool-specific configuration options
    """

    priority: int = 0
    conflicts_with: list[str] = field(default_factory=list)
    file_patterns: list[str] = field(default_factory=list)
    tool_type: ToolType = ToolType.LINTER
    options: dict[str, Any] = field(default_factory=dict)
