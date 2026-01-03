"""Console formatting utilities for Lintro.

This module contains formatting helpers extracted from console_logger.py
to improve maintainability and reduce file size.
"""

import re
from typing import Any

# Constants
TOOL_EMOJIS: dict[str, str] = {
    "ruff": "🦀",
    "prettier": "💅",
    "biome": "🌿",
    "darglint": "📝",
    "hadolint": "🐳",
    "yamllint": "📄",
    "black": "🖤",
    "pytest": "🧪",
    "markdownlint": "🔧",
    "actionlint": "🔧",
    "bandit": "🔧",
}
DEFAULT_EMOJI: str = "🔧"
BORDER_LENGTH: int = 70
INFO_BORDER_LENGTH: int = 70
DEFAULT_REMAINING_COUNT: int = 1

# Regex patterns used to parse tool outputs for remaining issue counts
# Centralized to avoid repeated long literals and to keep matching logic
# consistent across the module.
RE_CANNOT_AUTOFIX: re.Pattern[str] = re.compile(
    r"Found\s+(\d+)\s+issue(?:s)?\s+that\s+cannot\s+be\s+auto-fixed",
)
RE_REMAINING_OR_CANNOT: re.Pattern[str] = re.compile(
    r"(\d+)\s+(?:issue\(s\)\s+)?(?:that\s+cannot\s+be\s+auto-fixed|remaining)",
)


def get_tool_emoji(tool_name: str) -> str:
    """Get emoji for a tool.

    Args:
        tool_name: str: Name of the tool.

    Returns:
        str: Emoji for the tool.
    """
    return TOOL_EMOJIS.get(tool_name, DEFAULT_EMOJI)


def get_summary_value(
    summary: dict[str, Any] | object,
    key: str,
    default: int | float = 0,
) -> int | float:
    """Extract value from summary dict or object.

    Args:
        summary: Summary data as dict or dataclass.
        key: Attribute/key name.
        default: Default value if not found.

    Returns:
        int | float: The extracted value or default.
    """
    if isinstance(summary, dict):
        value = summary.get(key, default)
        return value if isinstance(value, (int, float)) else default
    value = getattr(summary, key, default)
    return value if isinstance(value, (int, float)) else default
