"""CLI argument parsing utilities for Lintro.

Functions for parsing tool lists and tool-specific options from command line arguments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lintro.tools.tool_enum import ToolEnum


def parse_tool_list(tools_str: str | None) -> list[ToolEnum]:
    """Parse a comma-separated list of core names into ToolEnum members.

    Args:
        tools_str: str | None: Comma-separated string of tool names, or None.

    Returns:
        list: List of ToolEnum members parsed from the input string.

    Raises:
        ValueError: If an invalid tool name is provided.
    """
    if not tools_str:
        return []
    # Import ToolEnum here to avoid circular import at module level
    from lintro.tools.tool_enum import ToolEnum

    result: list[ToolEnum] = []
    for t in tools_str.split(","):
        t = t.strip()
        if not t:
            continue
        try:
            result.append(ToolEnum[t.upper()])
        except KeyError:
            raise ValueError(f"Unknown tool: {t}") from None
    return result


def parse_tool_options(tool_options_str: str | None) -> dict[str, dict[str, str]]:
    """Parse tool-specific options.

    Args:
        tool_options_str: str | None: Comma-separated string of tool-specific
            options, or None.

    Returns:
        dict: Dictionary of parsed tool options.
    """
    if not tool_options_str:
        return {}

    options: dict[str, dict[str, str]] = {}
    for opt in tool_options_str.split(","):
        opt = opt.strip()
        if ":" in opt:
            tool_name, tool_opt = opt.split(":", 1)
            tool_name = tool_name.strip()
            tool_opt = tool_opt.strip()
            if "=" in tool_opt:
                opt_name, opt_value = tool_opt.split("=", 1)
                opt_name = opt_name.strip()
                opt_value = opt_value.strip()
                tool_options = options.setdefault(tool_name, {})
                tool_options[opt_name] = opt_value
    return options
