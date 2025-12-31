"""Unified configuration manager for Lintro.

This module provides a centralized configuration system that:
1. Reads global settings from [tool.lintro]
2. Reads native tool configs (for comparison/validation)
3. Reads tool-specific overrides from [tool.lintro.<tool>]
4. Computes effective config per tool with clear priority rules
5. Warns about inconsistencies between configs
6. Manages tool execution order (priority-based or alphabetical)

Priority order (highest to lowest):
1. CLI --tool-options (always wins)
2. [tool.lintro.<tool>] in pyproject.toml
3. [tool.lintro] global settings in pyproject.toml
4. Native tool config (e.g., .prettierrc, [tool.ruff])
5. Tool defaults
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Any, cast

from loguru import logger

from lintro.enums.tool_name import ToolName
from lintro.utils.config_loaders import (
    get_tool_order_config,
    load_lintro_global_config,
    load_lintro_tool_config,
    load_pyproject,
)
from lintro.utils.native_parsers import _load_native_tool_config

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# JSONC stripping moved to native_parsers.py
class ToolOrderStrategy(StrEnum):
    """Strategy for ordering tool execution."""

    PRIORITY = auto()  # Use tool priority values (formatters before linters)
    ALPHABETICAL = auto()  # Alphabetical by tool name
    CUSTOM = auto()  # Custom order defined in config


@dataclass
class ToolConfigInfo:
    """Information about a tool's configuration sources.

    Attributes:
        tool_name: Name of the tool
        native_config: Configuration from native tool config files
        lintro_tool_config: Configuration from [tool.lintro.<tool>]
        effective_config: Computed effective configuration
        warnings: List of warnings about configuration issues
        is_injectable: Whether Lintro can inject config to this tool
    """

    tool_name: str
    native_config: dict[str, Any] = field(default_factory=dict)
    lintro_tool_config: dict[str, Any] = field(default_factory=dict)
    effective_config: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    is_injectable: bool = True


# Global settings that Lintro can manage across tools
# Each setting maps to tool-specific config keys and indicates which tools
# support injection via Lintro config (vs requiring native config files)
GLOBAL_SETTINGS: dict[str, dict[str, Any]] = {
    "line_length": {
        "tools": {
            "ruff": "line-length",
            "black": "line-length",
            "markdownlint": "config.MD013.line_length",  # Nested in config object
            "prettier": "printWidth",
            "yamllint": "rules.line-length.max",  # Nested under rules.line-length.max
        },
        "injectable": {
            "ruff",
            "black",
            "markdownlint",
            "prettier",
            "yamllint",
        },
    },
    "target_python": {
        "tools": {
            "ruff": "target-version",
            "black": "target-version",
        },
        "injectable": {"ruff", "black"},
    },
    "indent_size": {
        "tools": {
            "prettier": "tabWidth",
            "ruff": "indent-width",
        },
        "injectable": {"prettier", "ruff"},
    },
    "quote_style": {
        "tools": {
            "ruff": "quote-style",  # Under [tool.ruff.format]
            "prettier": "singleQuote",  # Boolean: true for single quotes
        },
        "injectable": {"ruff", "prettier"},
    },
}

# Default tool priorities (lower = runs first)
# Formatters run before linters to avoid false positives
DEFAULT_TOOL_PRIORITIES: dict[str, int] = {
    "prettier": 10,  # Formatter - runs first
    "black": 15,  # Formatter
    "ruff": 20,  # Linter/Formatter hybrid
    "markdownlint": 30,  # Linter
    "yamllint": 35,  # Linter
    "darglint": 40,  # Linter
    "bandit": 45,  # Security linter
    "biome": 50,  # JavaScript/TypeScript/JSON/CSS linter
    "hadolint": 50,  # Docker linter
    "actionlint": 55,  # GitHub Actions linter
    "pytest": 100,  # Test runner - runs last
}


# Pyproject loading moved to config_loaders.py

# Native config loading moved to native_parsers.py


def _get_nested_value(config: dict[str, Any], key_path: str) -> Any:
    """Get a nested value from a config dict using dot notation.

    Args:
        config: Configuration dictionary
        key_path: Dot-separated key path (e.g., "line-length.max")

    Returns:
        Value at path, or None if not found
    """
    keys = key_path.split(".")
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


# Config loading functions moved to config_loaders.py


def get_tool_priority(tool_name: str) -> int:
    """Get the execution priority for a tool.

    Lower values run first. Formatters have lower priorities than linters.

    Args:
        tool_name: Name of the tool

    Returns:
        Priority value (lower = runs first)
    """
    order_config = get_tool_order_config()
    priority_overrides_raw = order_config.get("priority_overrides", {})
    priority_overrides = (
        priority_overrides_raw if isinstance(priority_overrides_raw, dict) else {}
    )
    # Normalize priority_overrides keys to lowercase for consistent lookup
    priority_overrides_normalized: dict[str, int] = {
        k.lower(): int(v) for k, v in priority_overrides.items() if isinstance(v, int)
    }
    tool_name_lower = tool_name.lower()

    # Check for override first
    if tool_name_lower in priority_overrides_normalized:
        return priority_overrides_normalized[tool_name_lower]

    # Use default priority
    return int(DEFAULT_TOOL_PRIORITIES.get(tool_name_lower, 50))


def get_ordered_tools(
    tool_names: list[str],
    tool_order: str | list[str] | None = None,
) -> list[str]:
    """Get tool names in execution order based on configured strategy.

    Args:
        tool_names: List of tool names to order
        tool_order: Optional override for tool order strategy. Can be:
            - "priority": Sort by tool priority (default)
            - "alphabetical": Sort alphabetically
            - list[str]: Custom order (tools in list come first)
            - None: Read strategy from config

    Returns:
        List of tool names in execution order
    """
    # Determine strategy and custom order
    strategy: ToolOrderStrategy
    if tool_order is None:
        order_config = get_tool_order_config()
        strategy_str = order_config.get("strategy", "priority")
        try:
            strategy = ToolOrderStrategy(strategy_str)
        except ValueError:
            logger.warning(
                f"Invalid tool order strategy '{strategy_str}', using 'priority'",
            )
            strategy = ToolOrderStrategy.PRIORITY
        custom_order = order_config.get("custom_order", [])
    elif isinstance(tool_order, list):
        strategy = ToolOrderStrategy.CUSTOM
        custom_order = tool_order
    else:
        try:
            strategy = ToolOrderStrategy(tool_order)
        except ValueError:
            logger.warning(
                f"Invalid tool order strategy '{tool_order}', using 'priority'",
            )
            strategy = ToolOrderStrategy.PRIORITY
        custom_order = []

    if strategy == ToolOrderStrategy.ALPHABETICAL:
        return sorted(tool_names, key=str.lower)

    if strategy == ToolOrderStrategy.CUSTOM:
        # Tools in custom_order come first (in that order), then remaining
        # by priority
        ordered: list[str] = []
        remaining = list(tool_names)

        for tool in custom_order:
            # Case-insensitive matching for custom order
            tool_lower = tool.lower()
            for t in remaining:
                if t.lower() == tool_lower:
                    ordered.append(t)
                    remaining.remove(t)
                    break

        # Add remaining tools by priority (consistent with default strategy)
        ordered.extend(
            sorted(remaining, key=lambda t: (get_tool_priority(t), t.lower())),
        )
        return ordered

    # Default: priority-based ordering
    return sorted(tool_names, key=lambda t: (get_tool_priority(t), t.lower()))


def get_effective_line_length(tool_name: str) -> int | None:
    """Get the effective line length for a specific tool.

    Priority:
    1. [tool.lintro.<tool>] line_length
    2. [tool.lintro] line_length
    3. [tool.ruff] line-length (as fallback source of truth)
    4. Native tool config
    5. None (use tool default)

    Args:
        tool_name: Name of the tool

    Returns:
        Effective line length, or None to use tool default
    """
    # 1. Check tool-specific lintro config
    lintro_tool = load_lintro_tool_config(tool_name)
    if "line_length" in lintro_tool and isinstance(lintro_tool["line_length"], int):
        return lintro_tool["line_length"]
    if "line-length" in lintro_tool and isinstance(lintro_tool["line-length"], int):
        return lintro_tool["line-length"]

    # 2. Check global lintro config
    lintro_global = load_lintro_global_config()
    if "line_length" in lintro_global and isinstance(
        lintro_global["line_length"],
        int,
    ):
        return lintro_global["line_length"]
    if "line-length" in lintro_global and isinstance(
        lintro_global["line-length"],
        int,
    ):
        return lintro_global["line-length"]

    # 3. Fall back to Ruff's line-length as source of truth
    pyproject = load_pyproject()
    tool_section_raw = pyproject.get("tool", {})
    tool_section = tool_section_raw if isinstance(tool_section_raw, dict) else {}
    ruff_config_raw = tool_section.get("ruff", {})
    ruff_config = ruff_config_raw if isinstance(ruff_config_raw, dict) else {}
    if "line-length" in ruff_config and isinstance(ruff_config["line-length"], int):
        return ruff_config["line-length"]
    if "line_length" in ruff_config and isinstance(ruff_config["line_length"], int):
        return ruff_config["line_length"]

    # 4. Check native tool config (for non-Ruff tools)
    native = _load_native_tool_config(tool_name)
    setting_key = GLOBAL_SETTINGS.get("line_length", {}).get("tools", {}).get(tool_name)
    if setting_key:
        native_value = _get_nested_value(native, setting_key)
        if isinstance(native_value, int):
            return native_value

    return None


def is_tool_injectable(tool_name: str) -> bool:
    """Check if Lintro can inject config to a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        True if Lintro can inject config via CLI or generated config file
    """
    return tool_name.lower() in GLOBAL_SETTINGS["line_length"]["injectable"]


def validate_config_consistency() -> list[str]:
    """Check for inconsistencies in line length settings across tools.

    Returns:
        List of warning messages about inconsistent configurations
    """
    warnings: list[str] = []
    effective_line_length = get_effective_line_length("ruff")

    if effective_line_length is None:
        return warnings

    # Check each tool's native config for mismatches
    for tool_name, setting_key in GLOBAL_SETTINGS["line_length"]["tools"].items():
        if tool_name == ToolName.RUFF.value:
            continue  # Skip Ruff (it's the source of truth)

        native = _load_native_tool_config(tool_name)
        native_value = _get_nested_value(native, setting_key)

        if native_value is not None and native_value != effective_line_length:
            injectable = is_tool_injectable(tool_name)
            if injectable:
                warnings.append(
                    f"{tool_name}: Native config has {setting_key}={native_value}, "
                    f"but Lintro will override with {effective_line_length}",
                )
            else:
                warnings.append(
                    f"⚠️  {tool_name}: Native config has {setting_key}={native_value}, "
                    f"differs from central line_length={effective_line_length}. "
                    f"Lintro cannot override this tool's native config - "
                    f"update manually for consistency.",
                )

    return warnings


def get_tool_config_summary() -> dict[str, ToolConfigInfo]:
    """Get a summary of configuration for all tools.

    Returns:
        Dictionary mapping tool names to their config info
    """
    tools = [
        "ruff",
        "black",
        "prettier",
        "yamllint",
        "markdownlint",
        "darglint",
        "bandit",
        "hadolint",
        "actionlint",
    ]
    summary: dict[str, ToolConfigInfo] = {}

    for tool_name in tools:
        info = ToolConfigInfo(
            tool_name=tool_name,
            native_config=_load_native_tool_config(tool_name),
            lintro_tool_config=load_lintro_tool_config(tool_name),
            is_injectable=is_tool_injectable(tool_name),
        )

        # Compute effective line_length
        effective_ll = get_effective_line_length(tool_name)
        if effective_ll is not None:
            info.effective_config["line_length"] = effective_ll

        summary[tool_name] = info

    # Add warnings
    warnings = validate_config_consistency()
    for warning in warnings:
        for tool_name in tools:
            if tool_name in warning.lower():
                summary[tool_name].warnings.append(warning)
                break

    return summary


# Config reporting functions moved to config_reporting.py


@dataclass
class UnifiedConfigManager:
    """Central configuration manager for Lintro.

    This class provides a unified interface for:
    - Loading and merging configurations from multiple sources
    - Computing effective configurations for each tool
    - Validating configuration consistency
    - Managing tool execution order

    Attributes:
        global_config: Global Lintro configuration from [tool.lintro]
        tool_configs: Per-tool configuration info
        warnings: List of configuration warnings
    """

    global_config: dict[str, Any] = field(default_factory=dict)
    tool_configs: dict[str, ToolConfigInfo] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize configuration manager."""
        self.refresh()

    def refresh(self) -> None:
        """Reload all configuration from files."""
        self.global_config = load_lintro_global_config()
        self.tool_configs = get_tool_config_summary()
        self.warnings = validate_config_consistency()

    def get_effective_line_length(self, tool_name: str) -> int | None:
        """Get effective line length for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Effective line length or None
        """
        return get_effective_line_length(tool_name)

    def get_tool_config(self, tool_name: str) -> ToolConfigInfo:
        """Get configuration info for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool configuration info
        """
        if tool_name not in self.tool_configs:
            self.tool_configs[tool_name] = ToolConfigInfo(
                tool_name=tool_name,
                native_config=_load_native_tool_config(tool_name),
                lintro_tool_config=load_lintro_tool_config(tool_name),
                is_injectable=is_tool_injectable(tool_name),
            )
        return self.tool_configs[tool_name]

    def get_ordered_tools(self, tool_names: list[str]) -> list[str]:
        """Get tools in execution order.

        Args:
            tool_names: List of tool names

        Returns:
            List of tool names in execution order
        """
        return get_ordered_tools(tool_names)

    def apply_config_to_tool(
        self,
        tool: Any,
        cli_overrides: dict[str, Any] | None = None,
    ) -> None:
        """Apply effective configuration to a tool instance.

        Priority order:
        1. CLI overrides (if provided)
        2. [tool.lintro.<tool>] config
        3. Global [tool.lintro] settings

        Args:
            tool: Tool instance with set_options method
            cli_overrides: Optional CLI override options

        Raises:
            TypeError: If tool configuration has type mismatches.
            ValueError: If tool configuration has invalid values.
        """
        tool_name = getattr(tool, "name", "").lower()
        if not tool_name:
            return

        # Start with global settings
        effective_opts: dict[str, Any] = {}

        # Apply global line_length if tool supports it
        if is_tool_injectable(tool_name):
            line_length = self.get_effective_line_length(tool_name)
            if line_length is not None:
                effective_opts["line_length"] = line_length

        # Apply tool-specific lintro config
        lintro_tool_config = load_lintro_tool_config(tool_name)
        effective_opts.update(lintro_tool_config)

        # Apply CLI overrides last (highest priority)
        if cli_overrides:
            effective_opts.update(cli_overrides)

        # Apply to tool
        if effective_opts:
            try:
                tool.set_options(**effective_opts)
                logger.debug(f"Applied config to {tool_name}: {effective_opts}")
            except (ValueError, TypeError) as e:
                # Configuration errors should be visible and re-raised
                logger.warning(
                    f"Configuration error for {tool_name}: {e}",
                    exc_info=True,
                )
                raise
            except Exception as e:
                # Other unexpected errors - log at warning but allow execution
                logger.warning(
                    f"Failed to apply config to {tool_name}: {e}",
                    exc_info=True,
                )

    def get_report(self) -> str:
        """Get configuration report.

        Returns:
            Formatted configuration report string
        """
        # Late import to avoid circular dependency
        from lintro.utils.config_reporting import get_config_report

        return cast(str, get_config_report())

    def print_report(self) -> None:
        """Print configuration report."""
        # Late import to avoid circular dependency
        from lintro.utils.config_reporting import print_config_report

        print_config_report()
