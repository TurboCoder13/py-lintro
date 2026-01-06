"""Tool execution order enum definitions.

This module defines the supported execution order strategies for tools.
"""

from __future__ import annotations

from enum import auto

from lintro.enums.uppercase_str_enum import UppercaseStrEnum


class ToolOrder(UppercaseStrEnum):
    """Supported tool execution order strategies.

    Values are uppercase string identifiers matching enum member names.
    """

    PRIORITY = auto()
    ALPHABETICAL = auto()
    CUSTOM = auto()


def normalize_tool_order(value: str | ToolOrder) -> ToolOrder:
    """Normalize a raw value to a ToolOrder enum.

    Args:
        value: str or ToolOrder to normalize.

    Returns:
        ToolOrder: Normalized enum value.

    Raises:
        ValueError: If the value is not a valid tool order.
    """
    if isinstance(value, ToolOrder):
        return value
    try:
        return ToolOrder[value.upper()]
    except KeyError as err:
        raise ValueError(
            f"Unknown tool order: {value!r}. Supported orders: {list(ToolOrder)}",
        ) from err
