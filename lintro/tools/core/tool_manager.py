"""Tool manager for Lintro."""

from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from lintro.models.core.tool import Tool
from lintro.tools.tool_enum import ToolEnum
from lintro.utils.unified_config import get_ordered_tools


@dataclass
class ToolManager:
    """Manager for core registration and execution.

    This class is responsible for:
    - Tool registration
    - Tool conflict resolution
    - Tool execution order (priority-based, alphabetical, or custom)
    - Tool configuration management

    Tool ordering is controlled by [tool.lintro].tool_order in pyproject.toml:
    - "priority" (default): Formatters run before linters based on priority values
    - "alphabetical": Tools run in alphabetical order by name
    - "custom": Tools run in order specified by [tool.lintro].tool_order_custom

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

        Tool ordering is controlled by [tool.lintro].tool_order in pyproject.toml:
        - "priority" (default): Formatters run before linters based on priority
        - "alphabetical": Tools run in alphabetical order by name
        - "custom": Tools run in order specified by [tool.lintro].tool_order_custom

        This method also handles:
        - Tool conflicts (unless ignore_conflicts is True)

        Args:
            tool_list: List of tools to order.
            ignore_conflicts: If True, skip conflict checking.

        Returns:
            List of ToolEnum members in execution order based on configured strategy.

        Raises:
            ValueError: If duplicate tools are found in tool_list.
        """
        if not tool_list:
            return []

        # Get core instances
        tools: dict[ToolEnum, Tool] = {name: self.get_tool(name) for name in tool_list}

        # Validate for duplicate tools
        seen_names: set[str] = set()
        duplicates: list[str] = []
        for tool in tool_list:
            tool_name_lower = tool.name.lower()
            if tool_name_lower in seen_names:
                duplicates.append(tool.name)
            else:
                seen_names.add(tool_name_lower)
        if duplicates:
            raise ValueError(
                f"Duplicate tools found in tool_list: {', '.join(duplicates)}",
            )

        # Convert ToolEnum to tool names for unified config ordering
        tool_names = [t.name.lower() for t in tool_list]
        ordered_names = get_ordered_tools(tool_names)

        # Map back to ToolEnum in the ordered sequence
        name_to_enum = {t.name.lower(): t for t in tool_list}
        sorted_tools = [
            name_to_enum[name] for name in ordered_names if name in name_to_enum
        ]

        # Validate that all requested tools are preserved
        original_names = {t.name.lower() for t in tool_list}
        sorted_names = {t.name.lower() for t in sorted_tools}
        missing_tools = original_names - sorted_names
        if missing_tools:
            # Append missing tools in their original order
            missing_enums = [t for t in tool_list if t.name.lower() in missing_tools]
            sorted_tools.extend(missing_enums)
            logger.warning(
                f"Some tools were not found in ordered list and appended: "
                f"{[t.name for t in missing_enums]}",
            )

        if ignore_conflicts:
            return sorted_tools

        # Build conflict graph
        conflict_graph: dict[ToolEnum, set[ToolEnum]] = {
            name: set() for name in tool_list
        }
        # Create mapping from tool name strings to ToolEnum members
        # Handle both lowercase strings and ToolEnum members in conflicts_with
        name_to_enum_map = {t.name.lower(): t for t in ToolEnum}
        for tool_enum_value in tool_list:
            tool_instance: Tool = tools[tool_enum_value]
            for conflict in tool_instance.config.conflicts_with:
                # Convert conflict string to ToolEnum if needed
                conflict_enum: ToolEnum | None = None
                if isinstance(conflict, str):
                    # Look up by lowercase name
                    conflict_enum = name_to_enum_map.get(conflict.lower())
                elif isinstance(conflict, ToolEnum):
                    # Already a ToolEnum member
                    conflict_enum = conflict
                # Only add to conflict graph if conflict_enum is in tool_list
                if conflict_enum is not None and conflict_enum in tool_list:
                    conflict_graph[tool_enum_value].add(conflict_enum)
                    conflict_graph[conflict_enum].add(tool_enum_value)

        # Resolve conflicts by keeping the first tool in ordered sequence
        result: list[ToolEnum] = []
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
