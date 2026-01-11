"""Configuration priority and ordering functions for Lintro.

This module provides functions for determining tool execution order,
priority-based configuration, and effective configuration values.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from lintro.utils.config import (
    get_tool_order_config,
    load_lintro_global_config,
    load_lintro_tool_config,
    load_pyproject,
)
from lintro.utils.config_constants import (
    DEFAULT_TOOL_PRIORITIES,
    GLOBAL_SETTINGS,
    ToolOrderStrategy,
)
from lintro.utils.native_parsers import _load_native_tool_config


def _get_nested_value(config: dict[str, Any], key_path: str) -> Any:
    """Get a nested value from a config dict using dot notation.

    Args:
        config: Configuration dictionary.
        key_path: Dot-separated key path (e.g., "line-length.max").

    Returns:
        Value at path, or None if not found.
    """
    keys = key_path.split(".")
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def get_tool_priority(tool_name: str) -> int:
    """Get the execution priority for a tool.

    Lower values run first. Formatters have lower priorities than linters.

    Args:
        tool_name: Name of the tool.

    Returns:
        Priority value (lower = runs first).
    """
    order_config = get_tool_order_config()
    priority_overrides_raw = order_config.get("priority_overrides", {})
    priority_overrides = (
        priority_overrides_raw if isinstance(priority_overrides_raw, dict) else {}
    )
    # Normalize priority_overrides keys to lowercase for consistent lookup
    priority_overrides_normalized: dict[str, int] = {
        k.lower(): int(v) for k, v in priority_overrides.items() if isinstance(v, int)
    }
    tool_name_lower = tool_name.lower()

    # Check for override first
    if tool_name_lower in priority_overrides_normalized:
        return priority_overrides_normalized[tool_name_lower]

    # Use default priority
    return int(DEFAULT_TOOL_PRIORITIES.get(tool_name_lower, 50))


def get_ordered_tools(
    tool_names: list[str],
    tool_order: str | list[str] | None = None,
) -> list[str]:
    """Get tool names in execution order based on configured strategy.

    Args:
        tool_names: List of tool names to order.
        tool_order: Optional override for tool order strategy. Can be:
            - "priority": Sort by tool priority (default).
            - "alphabetical": Sort alphabetically.
            - list[str]: Custom order (tools in list come first).
            - None: Read strategy from config.

    Returns:
        List of tool names in execution order.
    """
    # Determine strategy and custom order
    strategy: ToolOrderStrategy
    if tool_order is None:
        order_config = get_tool_order_config()
        strategy_str = order_config.get("strategy", "priority")
        try:
            strategy = ToolOrderStrategy(strategy_str)
        except ValueError:
            logger.warning(
                f"Invalid tool order strategy '{strategy_str}', using 'priority'",
            )
            strategy = ToolOrderStrategy.PRIORITY
        custom_order = order_config.get("custom_order", [])
    elif isinstance(tool_order, list):
        strategy = ToolOrderStrategy.CUSTOM
        custom_order = tool_order
    else:
        try:
            strategy = ToolOrderStrategy(tool_order)
        except ValueError:
            logger.warning(
                f"Invalid tool order strategy '{tool_order}', using 'priority'",
            )
            strategy = ToolOrderStrategy.PRIORITY
        custom_order = []

    if strategy == ToolOrderStrategy.ALPHABETICAL:
        return sorted(tool_names, key=str.lower)

    if strategy == ToolOrderStrategy.CUSTOM:
        # Tools in custom_order come first (in that order), then remaining
        # by priority
        ordered: list[str] = []
        remaining = list(tool_names)

        for tool in custom_order:
            # Case-insensitive matching for custom order
            tool_lower = tool.lower()
            matched = next((t for t in remaining if t.lower() == tool_lower), None)
            if matched:
                ordered.append(matched)
                remaining.remove(matched)

        # Add remaining tools by priority (consistent with default strategy)
        ordered.extend(
            sorted(remaining, key=lambda t: (get_tool_priority(t), t.lower())),
        )
        return ordered

    # Default: priority-based ordering
    return sorted(tool_names, key=lambda t: (get_tool_priority(t), t.lower()))


def get_effective_line_length(tool_name: str) -> int | None:
    """Get the effective line length for a specific tool.

    Priority:
    1. [tool.lintro.<tool>] line_length
    2. [tool.lintro] line_length
    3. [tool.ruff] line-length (as fallback source of truth)
    4. Native tool config
    5. None (use tool default)

    Args:
        tool_name: Name of the tool.

    Returns:
        Effective line length, or None to use tool default.
    """
    # 1. Check tool-specific lintro config
    lintro_tool = load_lintro_tool_config(tool_name)
    if "line_length" in lintro_tool and isinstance(lintro_tool["line_length"], int):
        return lintro_tool["line_length"]
    if "line-length" in lintro_tool and isinstance(lintro_tool["line-length"], int):
        return lintro_tool["line-length"]

    # 2. Check global lintro config
    lintro_global = load_lintro_global_config()
    if "line_length" in lintro_global and isinstance(
        lintro_global["line_length"],
        int,
    ):
        return lintro_global["line_length"]
    if "line-length" in lintro_global and isinstance(
        lintro_global["line-length"],
        int,
    ):
        return lintro_global["line-length"]

    # 3. Fall back to Ruff's line-length as source of truth
    pyproject = load_pyproject()
    tool_section_raw = pyproject.get("tool", {})
    tool_section = tool_section_raw if isinstance(tool_section_raw, dict) else {}
    ruff_config_raw = tool_section.get("ruff", {})
    ruff_config = ruff_config_raw if isinstance(ruff_config_raw, dict) else {}
    if "line-length" in ruff_config and isinstance(ruff_config["line-length"], int):
        return ruff_config["line-length"]
    if "line_length" in ruff_config and isinstance(ruff_config["line_length"], int):
        return ruff_config["line_length"]

    # 4. Check native tool config (for non-Ruff tools)
    native = _load_native_tool_config(tool_name)
    setting_key = GLOBAL_SETTINGS.get("line_length", {}).get("tools", {}).get(tool_name)
    if setting_key:
        native_value = _get_nested_value(native, setting_key)
        if isinstance(native_value, int):
            return native_value

    return None
