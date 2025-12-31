"""Tools value enum definitions.

This module defines special values for tool selection.
"""

from __future__ import annotations

from enum import StrEnum, auto


class ToolsValue(StrEnum):
    """Special values for tool selection.

    Values are lower-case string identifiers to align with CLI choices.
    """

    ALL = auto()


def normalize_tools_value(value: str | ToolsValue) -> ToolsValue:
    """Normalize a raw value to a ToolsValue enum.

    Args:
        value: str or ToolsValue to normalize.

    Returns:
        ToolsValue: Normalized enum value.

    Raises:
        ValueError: If the value is not a valid tools value.
    """
    if isinstance(value, ToolsValue):
        return value
    try:
        return ToolsValue[value.upper()]
    except KeyError as err:
        raise ValueError(
            f"Unknown tools value: {value!r}. Supported values: {list(ToolsValue)}",
        ) from err
