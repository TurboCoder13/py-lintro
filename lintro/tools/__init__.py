"""Tool implementations for Lintro."""

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import Tool
from lintro.models.core.tool_config import ToolConfig
from lintro.tools.core.tool_manager import ToolManager
from lintro.tools.implementations.tool_actionlint import ActionlintTool
from lintro.tools.implementations.tool_bandit import BanditTool
from lintro.tools.implementations.tool_black import BlackTool
from lintro.tools.implementations.tool_darglint import DarglintTool
from lintro.tools.implementations.tool_hadolint import HadolintTool
from lintro.tools.implementations.tool_prettier import PrettierTool
from lintro.tools.implementations.tool_ruff import RuffTool
from lintro.tools.implementations.tool_yamllint import YamllintTool
from lintro.tools.tool_enum import ToolEnum

# Create global core manager instance
tool_manager = ToolManager()

# Register all available tools using ToolEnum
AVAILABLE_TOOLS = {tool_enum: tool_enum.value for tool_enum in ToolEnum}


for tool_enum, tool_class in AVAILABLE_TOOLS.items():
    tool_manager.register_tool(tool_class)

# Consolidated exports
__all__ = [
    "Tool",
    "ToolConfig",
    "ToolType",
    "ToolManager",
    "ToolEnum",
    "tool_manager",
    "AVAILABLE_TOOLS",
    "BlackTool",
    "ActionlintTool",
    "BanditTool",
    "DarglintTool",
    "HadolintTool",
    "PrettierTool",
    "RuffTool",
    "YamllintTool",
]
