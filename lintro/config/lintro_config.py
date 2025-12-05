"""Lintro configuration dataclasses.

This module defines the configuration structure for .lintro-config.yaml.
The configuration follows a 4-tier model:

1. EXECUTION: What tools run and how (Lintro's core responsibility)
2. ENFORCE: Cross-cutting settings injected via CLI flags (overrides native configs)
3. DEFAULTS: Fallback config when no native config exists for a tool
4. TOOLS: Per-tool enable/disable and config source
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EnforceConfig:
    """Cross-cutting settings enforced across all tools via CLI flags.

    These settings override native tool configs to ensure consistency
    across different tools for shared concerns.

    Attributes:
        line_length: Line length limit injected via CLI flags.
            Injected as: --line-length (ruff, black), --print-width (prettier)
        target_python: Python version target (e.g., "py313").
            Injected as: --target-version (ruff, black)
    """

    line_length: int | None = None
    target_python: str | None = None


# Backward compatibility alias
GlobalConfig = EnforceConfig


@dataclass
class ExecutionConfig:
    """Execution control settings.

    Attributes:
        enabled_tools: List of tool names to run. If empty/None, all tools run.
        tool_order: Execution order strategy. One of:
            - "priority": Use default priority (formatters before linters)
            - "alphabetical": Alphabetical order
            - list[str]: Custom order as explicit list
        fail_fast: Stop on first tool failure.
        parallel: Run tools in parallel where possible (future).
    """

    enabled_tools: list[str] = field(default_factory=list)
    tool_order: str | list[str] = "priority"
    fail_fast: bool = False
    parallel: bool = False


@dataclass
class ToolConfig:
    """Configuration for a single tool.

    In the tiered model, tools use their native configs by default.
    Lintro only controls whether tools run and optionally specifies
    an explicit config source path.

    Attributes:
        enabled: Whether the tool is enabled.
        config_source: Optional explicit path to native config file.
            If not set, tool uses its own config discovery.
    """

    enabled: bool = True
    config_source: str | None = None


@dataclass
class LintroConfig:
    """Main Lintro configuration container.

    This is the root configuration object loaded from .lintro-config.yaml.
    Follows the 4-tier model:

    1. execution: What tools run and how
    2. enforce: Cross-cutting settings that override native configs
    3. defaults: Fallback config when no native config exists
    4. tools: Per-tool enable/disable and config source

    Attributes:
        execution: Execution control settings.
        enforce: Cross-cutting settings enforced via CLI flags.
        defaults: Fallback configs for tools without native configs.
        tools: Per-tool configuration, keyed by tool name.
        config_path: Path to the config file (set by loader).
    """

    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    enforce: EnforceConfig = field(default_factory=EnforceConfig)
    defaults: dict[str, dict[str, Any]] = field(default_factory=dict)
    tools: dict[str, ToolConfig] = field(default_factory=dict)
    config_path: str | None = None

    # Backward compatibility property
    @property
    def global_config(self) -> EnforceConfig:
        """Get enforce config (deprecated alias for backward compatibility).

        Returns:
            EnforceConfig: The enforce configuration.
        """
        return self.enforce

    def get_tool_config(self, tool_name: str) -> ToolConfig:
        """Get configuration for a specific tool.

        Args:
            tool_name: Name of the tool (e.g., "ruff", "prettier").

        Returns:
            ToolConfig: Tool configuration. Returns default config if not
                explicitly configured.
        """
        return self.tools.get(tool_name.lower(), ToolConfig())

    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a tool is enabled.

        A tool is enabled if:
        1. execution.enabled_tools is empty (all tools enabled), OR
        2. tool_name is in execution.enabled_tools, AND
        3. The tool's config has enabled=True (default)

        Args:
            tool_name: Name of the tool.

        Returns:
            bool: True if tool should run.
        """
        tool_lower = tool_name.lower()

        # Check execution.enabled_tools filter
        if self.execution.enabled_tools:
            enabled_lower = [t.lower() for t in self.execution.enabled_tools]
            if tool_lower not in enabled_lower:
                return False

        # Check tool-specific enabled flag
        tool_config = self.get_tool_config(tool_lower)
        return tool_config.enabled

    def get_tool_defaults(self, tool_name: str) -> dict[str, Any]:
        """Get default configuration for a tool.

        Used when the tool has no native config file.

        Args:
            tool_name: Name of the tool.

        Returns:
            dict[str, Any]: Default configuration or empty dict.
        """
        return self.defaults.get(tool_name.lower(), {})

    def get_effective_line_length(self, tool_name: str) -> int | None:
        """Get effective line length for a specific tool.

        In the tiered model, this simply returns the enforce.line_length
        value, which will be injected via CLI flags.

        Args:
            tool_name: Name of the tool (unused, kept for compatibility).

        Returns:
            int | None: Enforced line length or None.
        """
        return self.enforce.line_length

    def get_effective_target_python(self, tool_name: str) -> str | None:
        """Get effective Python target version for a specific tool.

        In the tiered model, this simply returns the enforce.target_python
        value, which will be injected via CLI flags.

        Args:
            tool_name: Name of the tool (unused, kept for compatibility).

        Returns:
            str | None: Enforced target version or None.
        """
        return self.enforce.target_python
