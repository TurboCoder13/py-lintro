"""Configuration loading utilities for Lintro.

Handles loading and parsing of configuration from pyproject.toml and other sources.
"""

import functools
import tomllib
from pathlib import Path
from typing import Any

from loguru import logger

__all__ = [
    "load_pyproject",
    "load_lintro_global_config",
    "get_tool_order_config",
    "load_lintro_tool_config",
]


@functools.lru_cache(maxsize=1)
def _find_pyproject() -> Path | None:
    """Search for pyproject.toml up the directory tree.

    Returns:
        Path to pyproject.toml if found, None otherwise.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / "pyproject.toml"
        if candidate.exists():
            return candidate
    return None


@functools.lru_cache(maxsize=1)
def load_pyproject() -> dict[str, Any]:
    """Load the full pyproject.toml.

    Uses LRU caching to avoid repeated file I/O operations.

    Returns:
        Full pyproject.toml contents as dict
    """
    pyproject_path = _find_pyproject()
    if not pyproject_path:
        logger.debug("No pyproject.toml found in current directory or parents")
        return {}
    try:
        with pyproject_path.open("rb") as f:
            return tomllib.load(f)
    except OSError as e:
        logger.warning(f"Failed to read pyproject.toml at {pyproject_path}: {e}")
        return {}
    except tomllib.TOMLDecodeError as e:
        logger.warning(f"Failed to parse pyproject.toml at {pyproject_path}: {e}")
        return {}


def _get_lintro_section() -> dict[str, Any]:
    """Extract the [tool.lintro] section from pyproject.toml.

    Returns:
        The tool.lintro section as a dict, or {} if not found or invalid.
    """
    pyproject = load_pyproject()
    tool_section_raw = pyproject.get("tool", {})
    tool_section = tool_section_raw if isinstance(tool_section_raw, dict) else {}
    lintro_config_raw = tool_section.get("lintro", {})
    return lintro_config_raw if isinstance(lintro_config_raw, dict) else {}


def load_lintro_global_config() -> dict[str, Any]:
    """Load global Lintro configuration from [tool.lintro].

    Returns:
        Global configuration dictionary (excludes tool-specific sections)
    """
    lintro_config = _get_lintro_section()

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
    lintro_config = _get_lintro_section()
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
