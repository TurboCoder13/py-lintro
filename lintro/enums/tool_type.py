"""Tool type definitions."""

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
    """

    LINTER = auto()
    FORMATTER = auto()
    TYPE_CHECKER = auto()
    DOCUMENTATION = auto()
    SECURITY = auto()
    INFRASTRUCTURE = auto()
