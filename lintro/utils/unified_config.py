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

import json
import tomllib
from dataclasses import dataclass, field
from enum import StrEnum, auto
from pathlib import Path
from typing import Any

from loguru import logger

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


def _strip_jsonc_comments(content: str) -> str:
    """Strip JSONC comments from content, preserving strings.

    This function safely removes // and /* */ comments from JSONC content
    while preserving comment-like sequences inside string values.

    Args:
        content: JSONC content as string

    Returns:
        Content with comments stripped

    Note:
        This is a simple implementation that handles most common cases.
        For complex JSONC with nested comments or edge cases, consider
        using a proper JSONC parser library (e.g., json5 or commentjson).
    """
    result: list[str] = []
    i = 0
    content_len = len(content)
    in_string = False
    escape_next = False
    in_block_comment = False

    while i < content_len:
        char = content[i]

        if escape_next:
            escape_next = False
            if not in_block_comment:
                result.append(char)
            i += 1
            continue

        if char == "\\" and in_string:
            escape_next = True
            if not in_block_comment:
                result.append(char)
            i += 1
            continue

        if char == '"' and not in_block_comment:
            in_string = not in_string
            result.append(char)
            i += 1
            continue

        if in_string:
            result.append(char)
            i += 1
            continue

        # Check for block comment start /* ... */
        if i < content_len - 1 and char == "/" and content[i + 1] == "*":
            in_block_comment = True
            i += 2
            continue

        # Check for block comment end */
        if (
            i > 0
            and i < content_len
            and char == "/"
            and content[i - 1] == "*"
            and in_block_comment
        ):
            in_block_comment = False
            i += 1
            continue

        # Check for line comment //
        if (
            i < content_len - 1
            and char == "/"
            and content[i + 1] == "/"
            and not in_block_comment
        ):
            # Skip to end of line
            while i < content_len and content[i] != "\n":
                i += 1
            # Include the newline if present
            if i < content_len:
                result.append("\n")
                i += 1
            continue

        if not in_block_comment:
            result.append(char)

        i += 1

    if in_block_comment:
        logger.warning("Unclosed block comment in JSONC content")

    return "".join(result)


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
    "eslint": 50,  # JavaScript/TypeScript linter
    "hadolint": 50,  # Docker linter
    "actionlint": 55,  # GitHub Actions linter
    "pytest": 100,  # Test runner - runs last
}


def _load_pyproject() -> dict[str, Any]:
    """Load the full pyproject.toml.

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


def _load_native_tool_config(tool_name: str) -> dict[str, Any]:
    """Load native configuration for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Native configuration dictionary
    """
    pyproject = _load_pyproject()
    tool_section = pyproject.get("tool", {})

    # Tools with pyproject.toml config
    if tool_name in ("ruff", "black", "bandit"):
        return tool_section.get(tool_name, {})

    # Yamllint: check native config files (not pyproject.toml)
    if tool_name == "yamllint":
        yamllint_config_files = [".yamllint", ".yamllint.yaml", ".yamllint.yml"]
        for config_file in yamllint_config_files:
            config_path = Path(config_file)
            if config_path.exists():
                if yaml is None:
                    logger.debug(
                        f"[UnifiedConfig] Found {config_file} but yaml not installed",
                    )
                    return {}
                try:
                    with config_path.open(encoding="utf-8") as f:
                        content = yaml.safe_load(f)
                        return content if isinstance(content, dict) else {}
                except (yaml.YAMLError, OSError) as e:
                    logger.debug(f"[UnifiedConfig] Failed to parse {config_file}: {e}")
        return {}

    # Prettier: check multiple config file formats
    if tool_name == "prettier":
        for config_file in [".prettierrc", ".prettierrc.json", "prettier.config.js"]:
            config_path = Path(config_file)
            if config_path.exists() and config_file.endswith(".json"):
                try:
                    with config_path.open(encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
            elif config_path.exists() and config_file == ".prettierrc":
                # Try parsing as JSON (common format)
                try:
                    with config_path.open(encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
        # Check package.json prettier field
        pkg_path = Path("package.json")
        if pkg_path.exists():
            try:
                with pkg_path.open(encoding="utf-8") as f:
                    pkg = json.load(f)
                    if "prettier" in pkg:
                        return pkg["prettier"]
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}

    # ESLint: check multiple config file formats
    if tool_name == "eslint":
        # Check flat config (ESLint 9+)
        flat_config = Path("eslint.config.js")
        if flat_config.exists():
            # Note: We can't easily parse JS files, so return empty dict
            # The tool will use the config natively
            return {}
        # Check legacy config files
        for config_file in [
            ".eslintrc.js",
            ".eslintrc.json",
            ".eslintrc.yaml",
            ".eslintrc.yml",
        ]:
            config_path = Path(config_file)
            if not config_path.exists():
                continue
            # Handle JSON files
            if config_file.endswith(".json"):
                try:
                    with config_path.open(encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
            # Handle YAML files
            elif config_file.endswith((".yaml", ".yml")):
                if yaml is None:
                    logger.debug(
                        f"[UnifiedConfig] Found {config_file} but yaml not installed",
                    )
                    continue
                try:
                    with config_path.open(encoding="utf-8") as f:
                        content = yaml.safe_load(f)
                        return content if isinstance(content, dict) else {}
                except (yaml.YAMLError, OSError) as e:
                    logger.debug(f"[UnifiedConfig] Failed to parse {config_file}: {e}")
        # Check package.json eslintConfig field
        pkg_path = Path("package.json")
        if pkg_path.exists():
            try:
                with pkg_path.open(encoding="utf-8") as f:
                    pkg = json.load(f)
                    if "eslintConfig" in pkg:
                        return pkg["eslintConfig"]
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}

    # Markdownlint: check config files
    if tool_name == "markdownlint":
        for config_file in [
            ".markdownlint.json",
            ".markdownlint.yaml",
            ".markdownlint.yml",
            ".markdownlint.jsonc",
        ]:
            config_path = Path(config_file)
            if not config_path.exists():
                continue

            # Handle JSON/JSONC files
            if config_file.endswith((".json", ".jsonc")):
                try:
                    with config_path.open(encoding="utf-8") as f:
                        content = f.read()
                        # Strip JSONC comments safely (preserves strings)
                        content = _strip_jsonc_comments(content)
                        return json.loads(content)
                except (json.JSONDecodeError, FileNotFoundError):
                    pass

            # Handle YAML files
            elif config_file.endswith((".yaml", ".yml")):
                if yaml is None:
                    logger.warning(
                        "PyYAML not available; cannot parse .markdownlint.yaml",
                    )
                    continue
                try:
                    with config_path.open(encoding="utf-8") as f:
                        content = yaml.safe_load(f)
                        # Handle multi-document YAML (coerce to dict)
                        if isinstance(content, list) and len(content) > 0:
                            content = content[0]
                        if isinstance(content, dict):
                            return content
                except Exception as e:  # noqa: BLE001
                    # Catch yaml.YAMLError and other exceptions
                    # (file I/O, parsing errors)
                    # Continue to next config file if this one fails to parse
                    logger.debug(
                        f"Failed to parse {config_path}: {type(e).__name__}",
                    )
                    pass
        return {}

    return {}


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


def load_lintro_global_config() -> dict[str, Any]:
    """Load global Lintro configuration from [tool.lintro].

    Returns:
        Global configuration dictionary (excludes tool-specific sections)
    """
    pyproject = _load_pyproject()
    lintro_config = pyproject.get("tool", {}).get("lintro", {})

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
    lintro_config = pyproject.get("tool", {}).get("lintro", {})
    return lintro_config.get(tool_name, {})


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


def get_tool_priority(tool_name: str) -> int:
    """Get the execution priority for a tool.

    Lower values run first. Formatters have lower priorities than linters.

    Args:
        tool_name: Name of the tool

    Returns:
        Priority value (lower = runs first)
    """
    order_config = get_tool_order_config()
    priority_overrides = order_config.get("priority_overrides", {})
    # Normalize priority_overrides keys to lowercase for consistent lookup
    priority_overrides_normalized = {
        k.lower(): v for k, v in priority_overrides.items()
    }
    tool_name_lower = tool_name.lower()

    # Check for override first
    if tool_name_lower in priority_overrides_normalized:
        return priority_overrides_normalized[tool_name_lower]

    # Use default priority
    return DEFAULT_TOOL_PRIORITIES.get(tool_name_lower, 50)


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
    if tool_order is None:
        order_config = get_tool_order_config()
        strategy = order_config.get("strategy", "priority")
        custom_order = order_config.get("custom_order", [])
    elif isinstance(tool_order, list):
        strategy = "custom"
        custom_order = tool_order
    else:
        strategy = tool_order
        custom_order = []

    if strategy == "alphabetical":
        return sorted(tool_names, key=str.lower)

    if strategy == "custom":
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
    if "line_length" in lintro_tool:
        return lintro_tool["line_length"]
    if "line-length" in lintro_tool:
        return lintro_tool["line-length"]

    # 2. Check global lintro config
    lintro_global = load_lintro_global_config()
    if "line_length" in lintro_global:
        return lintro_global["line_length"]
    if "line-length" in lintro_global:
        return lintro_global["line-length"]

    # 3. Fall back to Ruff's line-length as source of truth
    pyproject = _load_pyproject()
    ruff_config = pyproject.get("tool", {}).get("ruff", {})
    if "line-length" in ruff_config:
        return ruff_config["line-length"]
    if "line_length" in ruff_config:
        return ruff_config["line_length"]

    # 4. Check native tool config (for non-Ruff tools)
    native = _load_native_tool_config(tool_name)
    setting_key = GLOBAL_SETTINGS.get("line_length", {}).get("tools", {}).get(tool_name)
    if setting_key:
        native_value = _get_nested_value(native, setting_key)
        if native_value is not None:
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
        if tool_name == "ruff":
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


def get_config_report() -> str:
    """Generate a configuration report as a string.

    Returns:
        Formatted configuration report
    """
    summary = get_tool_config_summary()
    central_ll = get_effective_line_length("ruff")
    order_config = get_tool_order_config()

    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("LINTRO CONFIGURATION REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Global settings section
    lines.append("── Global Settings ──")
    lines.append(f"  Central line_length: {central_ll or 'Not configured'}")
    lines.append(f"  Tool order strategy: {order_config.get('strategy', 'priority')}")
    if order_config.get("custom_order"):
        lines.append(f"  Custom order: {', '.join(order_config['custom_order'])}")
    lines.append("")

    # Tool execution order section
    lines.append("── Tool Execution Order ──")
    tool_names = list(summary.keys())
    ordered_tools = get_ordered_tools(tool_names)
    for idx, tool_name in enumerate(ordered_tools, 1):
        priority = get_tool_priority(tool_name)
        lines.append(f"  {idx}. {tool_name} (priority: {priority})")
    lines.append("")

    # Per-tool configuration section
    lines.append("── Per-Tool Configuration ──")
    for tool_name, info in summary.items():
        injectable = "✅ Syncable" if info.is_injectable else "⚠️ Native only"
        effective = info.effective_config.get("line_length", "default")
        lines.append(f"  {tool_name}:")
        lines.append(f"    Status: {injectable}")
        lines.append(f"    Effective line_length: {effective}")
        if info.lintro_tool_config:
            lines.append(f"    Lintro config: {info.lintro_tool_config}")
        if info.native_config and tool_name not in ("ruff", "black", "bandit"):
            # Only show native config for tools with external config files
            lines.append(f"    Native config: {info.native_config}")
    lines.append("")

    # Warnings section
    all_warnings = validate_config_consistency()
    if all_warnings:
        lines.append("── Configuration Warnings ──")
        for warning in all_warnings:
            lines.append(f"  {warning}")
        lines.append("")
    else:
        lines.append("── Configuration Warnings ──")
        lines.append("  None - all configs consistent!")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def print_config_report() -> None:
    """Print a report of configuration status for all tools."""
    report = get_config_report()
    for line in report.split("\n"):
        if line.startswith("⚠️") or "Warning" in line:
            logger.warning(line)
        else:
            logger.info(line)


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
        return get_config_report()

    def print_report(self) -> None:
        """Print configuration report."""
        print_config_report()
