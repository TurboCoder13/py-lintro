"""Tool implementations for Lintro."""

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import Tool
from lintro.models.core.tool_config import ToolConfig
from lintro.tools.core.tool_manager import ToolManager
from lintro.tools.tool_enum import ToolEnum

# Import core implementations after Tool class definition to avoid circular imports
from lintro.tools.implementations.tool_darglint import DarglintTool
from lintro.tools.implementations.tool_hadolint import HadolintTool
from lintro.tools.implementations.tool_prettier import PrettierTool
from lintro.tools.implementations.tool_ruff import RuffTool
from lintro.tools.implementations.tool_yamllint import YamllintTool

# Create global core manager instance
tool_manager = ToolManager()

# Register all available tools using ToolEnum
AVAILABLE_TOOLS = {tool_enum: tool_enum.value for tool_enum in ToolEnum}

# Export tool classes for external use
__all__ = [
    "DarglintTool",
    "HadolintTool",
    "PrettierTool",
    "RuffTool",
    "YamllintTool",
    "tool_manager",
    "AVAILABLE_TOOLS",
    "Tool",
    "ToolConfig",
    "ToolManager",
    "ToolEnum",
    "ToolType",
]

for tool_enum, tool_class in AVAILABLE_TOOLS.items():
    tool_manager.register_tool(tool_class)

__all__ = [
    "Tool",
    "ToolConfig",
    "ToolType",
    "tool_manager",
    "AVAILABLE_TOOLS",
    "ToolEnum",
]
