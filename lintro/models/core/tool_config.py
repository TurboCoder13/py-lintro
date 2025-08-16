from dataclasses import dataclass, field

from lintro.enums.tool_type import ToolType


@dataclass
class ToolConfig:
    """Configuration for a core.

    Attributes:
        priority: int:
            Priority level (higher number = higher priority when resolving conflicts)
        conflicts_with: list[str]: List of tools this core conflicts with
        file_patterns: list[str]: List of file patterns this core should be applied to
        tool_type: ToolType: Type of core
        options: dict[str, object]: Tool-specific configuration options
    """

    priority: int = 0
    conflicts_with: list[str] = field(default_factory=list)
    file_patterns: list[str] = field(default_factory=list)
    tool_type: ToolType = ToolType.LINTER
    options: dict[str, object] = field(default_factory=dict)
