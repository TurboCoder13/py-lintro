"""Tool manager for Lintro."""

from dataclasses import dataclass, field
from typing import Any

from lintro.models.core.tool import Tool
from lintro.tools.tool_enum import ToolEnum


@dataclass
class ToolManager:
    """Manager for core registration and execution.

    This class is responsible for:
    - Tool registration
    - Tool conflict resolution
    - Tool execution order
    - Tool configuration management

    Attributes:
        _tools: Dictionary mapping core names to core classes
        _check_tools: Dictionary mapping core names to core classes that can check
        _fix_tools: Dictionary mapping core names to core classes that can fix
    """

    _tools: dict[ToolEnum, type[Tool]] = field(default_factory=dict)
    _check_tools: dict[ToolEnum, type[Tool]] = field(default_factory=dict)
    _fix_tools: dict[ToolEnum, type[Tool]] = field(default_factory=dict)

    def register_tool(
        self,
        tool_class: type[Tool],
    ) -> None:
        """Register a core class.

        Args:
            tool_class: The core class to register.

        Raises:
            ValueError: If the tool class is not found in ToolEnum.
        """
        tool = tool_class()
        # Find the ToolEnum member for this class
        tool_enum = next((e for e in ToolEnum if e.value is tool_class), None)
        if tool_enum is None:
            raise ValueError(f"Tool class {tool_class} not found in ToolEnum")
        self._tools[tool_enum] = tool_class
        # All tools can check (they all inherit from BaseTool with check method)
        self._check_tools[tool_enum] = tool_class
        # Only tools with can_fix=True can actually fix issues
        if tool.can_fix:
            self._fix_tools[tool_enum] = tool_class

    def get_tool(
        self,
        name: ToolEnum,
    ) -> Tool:
        """Get a core instance by name.

        Args:
            name: The name of the core to get

        Returns:
            The core instance

        Raises:
            ValueError: If the core is not found
        """
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")
        return self._tools[name]()

    def get_tool_execution_order(
        self,
        tool_list: list[ToolEnum],
        ignore_conflicts: bool = False,
    ) -> list[ToolEnum]:
        """Get the order in which tools should be executed.

        This method takes into account:
        - Tool conflicts
        - Alphabetical ordering
        - Tool dependencies

        Args:
            tool_list: List of core names to execute
            ignore_conflicts: Whether to ignore core conflicts

        Returns:
            List of core names in alphabetical execution order
        """
        if not tool_list:
            return []

        # Get core instances
        tools = {name: self.get_tool(name) for name in tool_list}

        # Sort tools alphabetically by name
        if ignore_conflicts:
            return sorted(
                tool_list,
                key=lambda name: name.name,
            )

        # Build conflict graph
        conflict_graph: dict[ToolEnum, set[ToolEnum]] = {
            name: set() for name in tool_list
        }
        for name, tool in tools.items():
            for conflict in tool.config.conflicts_with:
                if conflict in tool_list:
                    conflict_graph[name].add(conflict)
                    conflict_graph[conflict].add(name)

        # Sort tools alphabetically by name
        sorted_tools = sorted(
            tool_list,
            key=lambda name: name.name,
        )

        # Resolve conflicts by keeping the first alphabetical tool
        result = []
        for tool_name in sorted_tools:
            # Check if this core conflicts with any already selected tools
            conflicts = conflict_graph[tool_name] & set(result)
            if not conflicts:
                result.append(tool_name)

        return result

    def set_tool_options(
        self,
        name: ToolEnum,
        **options: Any,
    ) -> None:
        """Set options for a core.

        Args:
            name: The name of the core
            **options: The options to set
        """
        tool = self.get_tool(name)
        tool.set_options(**options)

    def get_available_tools(self) -> dict[ToolEnum, Tool]:
        """Get all available tools.

        Returns:
            Dictionary mapping core names to core classes
        """
        return {name: tool_class() for name, tool_class in self._tools.items()}

    def get_check_tools(self) -> dict[ToolEnum, Tool]:
        """Get all tools that can check files.

        Returns:
            Dictionary mapping core names to core instances
        """
        return {name: tool_class() for name, tool_class in self._check_tools.items()}

    def get_fix_tools(self) -> dict[ToolEnum, Tool]:
        """Get all tools that can fix files.

        Returns:
            Dictionary mapping core names to core instances
        """
        return {name: tool_class() for name, tool_class in self._fix_tools.items()}
