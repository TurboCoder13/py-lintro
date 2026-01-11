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

This module re-exports from split submodules for backwards compatibility.
"""

from __future__ import annotations

# Re-export from config module
from lintro.utils.config import (
    get_tool_order_config,
    load_lintro_global_config,
    load_lintro_tool_config,
)

# Re-export from config_constants module
from lintro.utils.config_constants import (
    DEFAULT_TOOL_PRIORITIES,
    GLOBAL_SETTINGS,
    ToolConfigInfo,
    ToolOrderStrategy,
)

# Re-export from config_priority module
from lintro.utils.config_priority import (
    _get_nested_value,
    get_effective_line_length,
    get_ordered_tools,
    get_tool_priority,
)

# Re-export from config_validation module
from lintro.utils.config_validation import (
    get_tool_config_summary,
    is_tool_injectable,
    validate_config_consistency,
)

# Re-export from native_parsers module
from lintro.utils.native_parsers import _load_native_tool_config

# Re-export from unified_config_manager module
from lintro.utils.unified_config_manager import UnifiedConfigManager

__all__ = [
    # From config module
    "get_tool_order_config",
    "load_lintro_global_config",
    "load_lintro_tool_config",
    # From config_constants module
    "DEFAULT_TOOL_PRIORITIES",
    "GLOBAL_SETTINGS",
    "ToolConfigInfo",
    "ToolOrderStrategy",
    # From config_priority module
    "_get_nested_value",
    "get_effective_line_length",
    "get_ordered_tools",
    "get_tool_priority",
    # From config_validation module
    "get_tool_config_summary",
    "is_tool_injectable",
    "validate_config_consistency",
    # From native_parsers module
    "_load_native_tool_config",
    # From unified_config_manager module
    "UnifiedConfigManager",
]
