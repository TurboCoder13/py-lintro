"""Configuration validation functions for Lintro.

This module provides functions for validating configuration consistency
across tools and checking tool injectability.
"""

from __future__ import annotations

from lintro.enums.tool_name import ToolName
from lintro.utils.config import load_lintro_tool_config
from lintro.utils.config_constants import GLOBAL_SETTINGS, ToolConfigInfo
from lintro.utils.config_priority import _get_nested_value, get_effective_line_length
from lintro.utils.native_parsers import _load_native_tool_config


def is_tool_injectable(tool_name: str | ToolName) -> bool:
    """Check if Lintro can inject config to a tool.

    Args:
        tool_name: Name of the tool (string or ToolName enum).

    Returns:
        True if Lintro can inject config via CLI or generated config file.
    """
    injectable_set: set[ToolName] = GLOBAL_SETTINGS["line_length"]["injectable"]
    # ToolName is a StrEnum, so string comparison works
    tool_name_lower = tool_name.lower() if isinstance(tool_name, str) else tool_name
    return tool_name_lower in injectable_set


def validate_config_consistency() -> list[str]:
    """Check for inconsistencies in line length settings across tools.

    Returns:
        List of warning messages about inconsistent configurations.
    """
    warnings: list[str] = []
    effective_line_length = get_effective_line_length(ToolName.RUFF)

    if effective_line_length is None:
        return warnings

    # Check each tool's native config for mismatches
    tools_config: dict[ToolName, str] = GLOBAL_SETTINGS["line_length"]["tools"]
    for tool_name, setting_key in tools_config.items():
        if tool_name == ToolName.RUFF:
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
                    f"Warning: {tool_name}: Native config has "
                    f"{setting_key}={native_value}, "
                    f"differs from central line_length={effective_line_length}. "
                    f"Lintro cannot override this tool's native config - "
                    f"update manually for consistency.",
                )

    return warnings


def get_tool_config_summary() -> dict[str, ToolConfigInfo]:
    """Get a summary of configuration for all tools.

    Returns:
        Dictionary mapping tool names to their config info.
    """
    tools = [
        ToolName.RUFF,
        ToolName.BLACK,
        ToolName.PRETTIER,
        ToolName.YAMLLINT,
        ToolName.MARKDOWNLINT,
        ToolName.DARGLINT,
        ToolName.BANDIT,
        ToolName.HADOLINT,
        ToolName.ACTIONLINT,
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
