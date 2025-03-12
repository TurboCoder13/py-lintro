"""Tool interfaces for Lintro."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolConfig:
    """Configuration for a tool, including conflict resolution settings."""

    # Priority level (higher number = higher priority when resolving conflicts)
    priority: int = 0

    # List of tools this tool conflicts with
    conflicts_with: list[str] = field(default_factory=list)

    # List of file patterns this tool should be applied to
    file_patterns: list[str] = field(default_factory=list)

    # Tool-specific configuration options
    options: dict[str, Any] = field(default_factory=dict)


class Tool(ABC):
    """Base class for all linting and formatting tools."""

    name: str
    description: str
    can_fix: bool
    config: ToolConfig = ToolConfig()

    def set_options(
        self,
        exclude_patterns: list[str] | None = None,
        include_venv: bool = False,
    ):
        """
        Set options for the tool.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
        """
        self.exclude_patterns = exclude_patterns or []
        self.include_venv = include_venv

    @abstractmethod
    def check(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Check the given paths for issues.

        Args:
            paths: List of file or directory paths to check

        Returns:
            Tuple of (success, output)
            - success: True if no issues were found, False otherwise
            - output: Output from the tool
        """
        pass

    @abstractmethod
    def fix(
        self,
        paths: list[str],
    ) -> tuple[bool, str]:
        """
        Fix issues in the given paths.

        Args:
            paths: List of file or directory paths to fix

        Returns:
            Tuple of (success, output)
            - success: True if fixes were applied successfully, False otherwise
            - output: Output from the tool
        """
        pass


# Import all tool implementations
# These need to be imported after the Tool class is defined to avoid circular imports
from lintro.tools.black import BlackTool  # noqa: E402
from lintro.tools.darglint import DarglintTool  # noqa: E402
from lintro.tools.flake8 import Flake8Tool  # noqa: E402
from lintro.tools.isort import IsortTool  # noqa: E402

# Register all available tools
AVAILABLE_TOOLS = {
    "black": BlackTool(),
    "isort": IsortTool(),
    "flake8": Flake8Tool(),
    "darglint": DarglintTool(),
}

# Tools that can fix issues
FIX_TOOLS = {name: tool for name, tool in AVAILABLE_TOOLS.items() if tool.can_fix}

# Tools that can only check for issues
CHECK_TOOLS = AVAILABLE_TOOLS


def resolve_tool_conflicts(selected_tools: list[str]) -> list[str]:
    """
    Resolve conflicts between tools and return a list of tools to run
    in the correct order.

    Args:
        selected_tools: List of tool names to check for conflicts

    Returns:
        List of tool names to run, ordered by priority (highest first)
    """
    # Filter to only include available tools
    valid_tools = [name for name in selected_tools if name in AVAILABLE_TOOLS]

    # Check for conflicts
    conflicts = {}
    for tool_name in valid_tools:
        tool = AVAILABLE_TOOLS[tool_name]
        for conflict in tool.config.conflicts_with:
            if conflict in valid_tools:
                if tool_name not in conflicts:
                    conflicts[tool_name] = []
                conflicts[tool_name].append(conflict)

    # If there are conflicts, resolve them based on priority
    if conflicts:
        resolved_tools = []
        # Sort tools by priority (highest first)
        sorted_tools = sorted(
            valid_tools,
            key=lambda name: AVAILABLE_TOOLS[name].config.priority,
            reverse=True,
        )

        # Add tools in priority order, skipping those that conflict with
        # higher priority tools
        excluded_tools = set()
        for tool_name in sorted_tools:
            if tool_name in excluded_tools:
                continue

            resolved_tools.append(tool_name)

            # Add any conflicting tools to the excluded set
            if tool_name in conflicts:
                excluded_tools.update(conflicts[tool_name])

        return resolved_tools

    # If no conflicts, return the original list
    return valid_tools


def get_tool_execution_order(selected_tools: list[str]) -> list[str]:
    """
    Get the order in which tools should be executed, based on their priorities.

    Args:
        selected_tools: List of tool names to order

    Returns:
        List of tool names in execution order
    """
    # Resolve any conflicts first
    resolved_tools = resolve_tool_conflicts(selected_tools)

    # Sort by priority (highest first)
    return sorted(
        resolved_tools,
        key=lambda name: AVAILABLE_TOOLS[name].config.priority,
        reverse=True,
    )
