"""Configuration loading utilities for Lintro.

Handles loading and parsing of configuration from pyproject.toml and other sources.
"""

import functools
import tomllib
from pathlib import Path
from typing import Any


@functools.lru_cache(maxsize=1)
def _load_pyproject() -> dict[str, Any]:
    """Load the full pyproject.toml.

    Uses LRU caching to avoid repeated file I/O operations.

    Returns:
        Full pyproject.toml contents as dict
    """
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return {}
    try:
        with pyproject_path.open("rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def load_lintro_global_config() -> dict[str, Any]:
    """Load global Lintro configuration from [tool.lintro].

    Returns:
        Global configuration dictionary (excludes tool-specific sections)
    """
    pyproject = _load_pyproject()
    tool_section_raw = pyproject.get("tool", {})
    tool_section = tool_section_raw if isinstance(tool_section_raw, dict) else {}
    lintro_config_raw = tool_section.get("lintro", {})
    lintro_config = lintro_config_raw if isinstance(lintro_config_raw, dict) else {}

    # Filter out known tool-specific sections
    tool_sections = {
        "ruff",
        "black",
        "prettier",
        "yamllint",
        "markdownlint",
        "markdownlint-cli2",
        "bandit",
        "darglint",
        "hadolint",
        "actionlint",
        "pytest",
        "post_checks",
        "versions",
    }

    return {k: v for k, v in lintro_config.items() if k not in tool_sections}


def load_lintro_tool_config(tool_name: str) -> dict[str, Any]:
    """Load tool-specific Lintro config from [tool.lintro.<tool>].

    Args:
        tool_name: Name of the tool

    Returns:
        Tool-specific Lintro configuration
    """
    pyproject = _load_pyproject()
    tool_section_raw = pyproject.get("tool", {})
    tool_section = tool_section_raw if isinstance(tool_section_raw, dict) else {}
    lintro_config_raw = tool_section.get("lintro", {})
    lintro_config = lintro_config_raw if isinstance(lintro_config_raw, dict) else {}
    tool_config = lintro_config.get(tool_name, {})
    return tool_config if isinstance(tool_config, dict) else {}


def get_tool_order_config() -> dict[str, Any]:
    """Get tool ordering configuration from [tool.lintro].

    Returns:
        Tool ordering configuration with keys:
        - strategy: "priority", "alphabetical", or "custom"
        - custom_order: list of tool names (for custom strategy)
        - priority_overrides: dict of tool -> priority (for priority strategy)
    """
    global_config = load_lintro_global_config()

    return {
        "strategy": global_config.get("tool_order", "priority"),
        "custom_order": global_config.get("tool_order_custom", []),
        "priority_overrides": global_config.get("tool_priorities", {}),
    }
