"""Canonical tool name definitions.

Provides a stable set of identifiers for tools used across the codebase.
"""

from __future__ import annotations

from enum import StrEnum, auto


class ToolName(StrEnum):
    """Supported tool identifiers in lower-case values."""

    ACTIONLINT = auto()
    BANDIT = auto()
    BIOME = auto()
    BLACK = auto()
    CLIPPY = auto()
    DARGLINT = auto()
    GITLEAKS = auto()
    HADOLINT = auto()
    MARKDOWNLINT = auto()
    MYPY = auto()
    PRETTIER = auto()
    PYTEST = auto()
    RUFF = auto()
    SEMGREP = auto()
    SHELLCHECK = auto()
    SHFMT = auto()
    SQLFLUFF = auto()
    TAPLO = auto()
    YAMLLINT = auto()


def normalize_tool_name(value: str | ToolName) -> ToolName:
    """Normalize a raw name to ToolName.

    Args:
        value: Tool name as str or ToolName.

    Returns:
        ToolName: Normalized enum member.

    Raises:
        ValueError: If the value is not a valid tool name.
    """
    if isinstance(value, ToolName):
        return value
    try:
        return ToolName[value.upper()]
    except KeyError as err:
        raise ValueError(
            f"Unknown tool name: {value!r}. Supported tools: {list(ToolName)}",
        ) from err
