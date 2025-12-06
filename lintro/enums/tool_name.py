"""Canonical tool name definitions.

Provides a stable set of identifiers for tools used across the codebase.
"""

from __future__ import annotations

from enum import StrEnum, auto


class ToolName(StrEnum):
    """Supported tool identifiers in lower-case values."""

    DARGLINT = auto()
    ESLINT = auto()
    HADOLINT = auto()
    MARKDOWNLINT = auto()
    PRETTIER = auto()
    RUFF = auto()
    YAMLLINT = auto()


def normalize_tool_name(value: str | ToolName) -> ToolName:
    """Normalize a raw name to ToolName.

    Args:
        value: Tool name as str or ToolName.

    Returns:
        ToolName: Normalized enum member.
    """
    if isinstance(value, ToolName):
        return value
    try:
        return ToolName[value.upper()]
    except Exception:
        # Conservative default if unknown
        return ToolName.RUFF
