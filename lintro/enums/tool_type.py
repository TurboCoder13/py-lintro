"""Tool type definitions."""

from __future__ import annotations

from enum import Flag, auto


class ToolType(Flag):
    """Tool type definitions.

    This enum defines the different types of tools that can be used in Lintro.
    Tools can be of multiple types (e.g., a core can be both a linter and a formatter),
    which is why this is a Flag enum rather than a regular Enum.

    Attributes:
        LINTER = Tool that checks code for issues
        FORMATTER = Tool that formats code
        TYPE_CHECKER = Tool that checks types
        DOCUMENTATION = Tool that checks documentation
        SECURITY = Tool that checks for security issues
        INFRASTRUCTURE = Tool that checks infrastructure code
        TEST_RUNNER = Tool that runs tests
    """

    LINTER = auto()
    FORMATTER = auto()
    TYPE_CHECKER = auto()
    DOCUMENTATION = auto()
    SECURITY = auto()
    INFRASTRUCTURE = auto()
    TEST_RUNNER = auto()


def normalize_tool_type(value: str | ToolType) -> ToolType:
    """Normalize a raw value to a ToolType enum.

    For enum instances, combined Flag values
    (e.g., ToolType.LINTER | ToolType.FORMATTER) are preserved.
    For string inputs, attempts to match a single enum name
    (case-insensitive, e.g., "LINTER"). String inputs do not support
    combination syntax like "LINTER|FORMATTER".

    Args:
        value: str or ToolType to normalize.

    Returns:
        ToolType: Normalized enum value.

    Raises:
        ValueError: If the value is not a valid tool type.
    """
    if isinstance(value, ToolType):
        return value
    if isinstance(value, str):
        try:
            return ToolType[value.upper()]
        except KeyError as err:
            supported = f"Supported types: {list(ToolType)}"
            raise ValueError(
                f"Unknown tool type: {value!r}. {supported}",
            ) from err
    raise ValueError(f"Invalid tool type: {value!r}. Expected str or ToolType.")
