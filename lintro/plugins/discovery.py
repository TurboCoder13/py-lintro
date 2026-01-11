"""Tool discovery for builtin and external plugins.

This module handles discovering and loading Lintro tools from:
1. Built-in tool definitions (lintro/tools/definitions/)
2. External plugins via Python entry points (lintro.plugins)

Example:
    >>> from lintro.plugins.discovery import discover_all_tools
    >>> discover_all_tools()  # Loads all available tools
"""

from __future__ import annotations

import importlib
import importlib.metadata
from pathlib import Path

from loguru import logger

from lintro.plugins.protocol import LintroPlugin
from lintro.plugins.registry import ToolRegistry

# Path to builtin tool definitions
BUILTIN_DEFINITIONS_PATH = Path(__file__).parent.parent / "tools" / "definitions"

# Entry point group for external plugins
ENTRY_POINT_GROUP = "lintro.plugins"

# Track whether discovery has been performed
_discovered: bool = False


def discover_builtin_tools() -> int:
    """Load all builtin tool definitions.

    This function imports all Python modules in the tools/definitions/
    directory, which triggers the @register_tool decorators.

    Returns:
        Number of tool modules loaded.

    Note:
        Each tool definition file should use the @register_tool decorator
        to register itself with the ToolRegistry.
    """
    loaded_count = 0

    if not BUILTIN_DEFINITIONS_PATH.exists():
        logger.warning(
            f"Builtin definitions path not found: {BUILTIN_DEFINITIONS_PATH}",
        )
        return loaded_count

    for py_file in BUILTIN_DEFINITIONS_PATH.glob("*.py"):
        if py_file.name.startswith("_"):
            continue

        module_name = f"lintro.tools.definitions.{py_file.stem}"
        try:
            importlib.import_module(module_name)
            logger.debug(f"Loaded builtin tool: {py_file.stem}")
            loaded_count += 1
        except ImportError as e:
            logger.warning(f"Failed to import {module_name}: {e}")
        except (AttributeError, TypeError, ValueError) as e:
            logger.error(f"Error loading {module_name}: {type(e).__name__}: {e}")

    logger.debug(f"Loaded {loaded_count} builtin tool definitions")
    return loaded_count


def discover_external_plugins() -> int:
    """Load external plugins via entry points.

    External plugins can register themselves by defining an entry point
    in their pyproject.toml or setup.py:

        [project.entry-points."lintro.plugins"]
        my-tool = "my_package.plugin:MyToolPlugin"

    Returns:
        Number of external plugins loaded.

    Note:
        External plugins should be classes that implement LintroPlugin.
        They will be automatically registered with the ToolRegistry.
    """
    loaded_count = 0

    try:
        entry_points = importlib.metadata.entry_points(group=ENTRY_POINT_GROUP)
    except (TypeError, AttributeError, KeyError) as e:
        logger.debug(f"No entry points found or error accessing them: {e}")
        return loaded_count

    for ep in entry_points:
        try:
            plugin_class = ep.load()

            # Validate that it's a proper plugin class
            if not isinstance(plugin_class, type):
                logger.warning(
                    f"Entry point {ep.name!r} does not point to a class, skipping",
                )
                continue

            # Check if it implements LintroPlugin protocol (without instantiating)
            # LintroPlugin is @runtime_checkable, so issubclass works
            if not issubclass(plugin_class, LintroPlugin):
                logger.warning(
                    f"Entry point {ep.name!r} class does not implement LintroPlugin, "
                    "skipping",
                )
                continue

            # Register the plugin if not already registered
            if not ToolRegistry.is_registered(ep.name):
                ToolRegistry.register(plugin_class)
                logger.info(f"Loaded external plugin: {ep.name}")
                loaded_count += 1
            else:
                logger.debug(f"Plugin {ep.name!r} already registered, skipping")

        except (ImportError, AttributeError, TypeError, RuntimeError) as e:
            logger.warning(f"Failed to load plugin {ep.name!r}: {e}")

    logger.debug(f"Loaded {loaded_count} external plugins")
    return loaded_count


def discover_all_tools(force: bool = False) -> int:
    """Discover and register all available tools.

    This function loads both builtin tools and external plugins.
    It's safe to call multiple times - subsequent calls are no-ops
    unless force=True.

    Args:
        force: If True, re-discover even if already discovered.

    Returns:
        Total number of tools loaded.

    Example:
        >>> from lintro.plugins.discovery import discover_all_tools
        >>> count = discover_all_tools()
        >>> print(f"Loaded {count} tools")
    """
    global _discovered

    if _discovered and not force:
        logger.debug("Tools already discovered, skipping")
        return 0

    logger.debug("Discovering tools...")

    # Discover builtin tools first
    builtin_count = discover_builtin_tools()

    # Then discover external plugins (skips already-registered tool names)
    external_count = discover_external_plugins()

    total = builtin_count + external_count
    _discovered = True

    logger.info(
        f"Tool discovery complete: {builtin_count} builtin, {external_count} external",
    )
    return total


def is_discovered() -> bool:
    """Check if tool discovery has been performed.

    Returns:
        True if discover_all_tools() has been called, False otherwise.
    """
    return _discovered


def reset_discovery() -> None:
    """Reset the discovery state.

    This is primarily useful for testing.
    """
    global _discovered
    _discovered = False
