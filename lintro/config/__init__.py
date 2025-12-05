"""Lintro configuration module.

This module provides a tiered configuration system:
1. EXECUTION: What tools run and how
2. ENFORCE: Cross-cutting settings injected via CLI flags
3. DEFAULTS: Fallback config when no native config exists
4. TOOLS: Per-tool enable/disable and config source

Key components:
- LintroConfig: Main configuration dataclass
- EnforceConfig: Cross-cutting settings enforced via CLI
- ConfigLoader: Loads .lintro-config.yaml
- ToolConfigGenerator: CLI injection and defaults generation
"""

from lintro.config.config_loader import (
    clear_config_cache,
    get_config,
    get_default_config,
    load_config,
)
from lintro.config.lintro_config import (
    EnforceConfig,
    ExecutionConfig,
    GlobalConfig,
    LintroConfig,
    ToolConfig,
)
from lintro.config.tool_config_generator import (
    cleanup_temp_config,
    generate_defaults_config,
    generate_tool_config,
    get_config_injection_args,
    get_defaults_injection_args,
    get_enforce_cli_args,
    get_no_auto_config_args,
    has_native_config,
)

__all__ = [
    # Config dataclasses
    "EnforceConfig",
    "ExecutionConfig",
    "GlobalConfig",  # Deprecated alias for EnforceConfig
    "LintroConfig",
    "ToolConfig",
    # Config loading
    "clear_config_cache",
    "get_config",
    "get_default_config",
    "load_config",
    # New tiered model functions
    "get_enforce_cli_args",
    "has_native_config",
    "generate_defaults_config",
    "get_defaults_injection_args",
    # Deprecated functions (kept for backward compatibility)
    "cleanup_temp_config",
    "generate_tool_config",
    "get_config_injection_args",
    "get_no_auto_config_args",
]
