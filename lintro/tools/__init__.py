"""Tool implementations for Lintro.

This module provides the plugin-based tool system for Lintro.
Tools are automatically discovered and registered via the plugin registry.
"""

from lintro.enums.tool_type import ToolType
from lintro.plugins import LintroPlugin, ToolDefinition, ToolRegistry
from lintro.tools.core.tool_manager import ToolManager

# Create global tool manager instance
tool_manager = ToolManager()

# Consolidated exports
__all__ = [
    "LintroPlugin",
    "ToolDefinition",
    "ToolRegistry",
    "ToolType",
    "ToolManager",
    "tool_manager",
]
