"""Lintro configuration dataclasses.

This module defines the configuration structure for .lintro-config.yaml.
Lintro acts as the master configuration source, and native tool configs
are ignored unless explicitly referenced via config_source.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GlobalConfig:
    """Global settings that cascade to all supporting tools.

    Attributes:
        line_length: Line length limit applied to all tools that support it.
            Maps to: ruff line-length, black line-length, prettier printWidth,
            markdownlint MD013.line_length, yamllint line-length.max
        target_python: Python version target (e.g., "py313").
            Maps to: ruff target-version, black target-version
        indent_size: Indentation size in spaces (future).
        quote_style: Quote style preference (future).
    """

    line_length: int | None = None
    target_python: str | None = None
    indent_size: int | None = None
    quote_style: str | None = None


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

    Attributes:
        enabled: Whether the tool is enabled.
        config_source: Path to native config file to inherit from.
            If not set, tool receives only Lintro-managed config.
        overrides: Settings that override config_source values.
            Always applied on top of inherited config.
        settings: Direct tool settings (merged with overrides).
    """

    enabled: bool = True
    config_source: str | None = None
    overrides: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)

    def get_effective_settings(self) -> dict[str, Any]:
        """Get merged settings with overrides applied.

        Returns:
            dict[str, Any]: Merged settings dictionary.
        """
        result = dict(self.settings)
        result.update(self.overrides)
        return result


@dataclass
class LintroConfig:
    """Main Lintro configuration container.

    This is the root configuration object loaded from .lintro-config.yaml.
    Lintro is the master - all tool execution is controlled by this config.

    Attributes:
        global_config: Global settings that cascade to tools.
        execution: Execution control settings.
        tools: Per-tool configuration, keyed by tool name.
        config_path: Path to the config file (set by loader).
    """

    global_config: GlobalConfig = field(default_factory=GlobalConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    tools: dict[str, ToolConfig] = field(default_factory=dict)
    config_path: str | None = None

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

    def get_effective_line_length(self, tool_name: str) -> int | None:
        """Get effective line length for a specific tool.

        Priority:
        1. Tool-specific override
        2. Tool-specific setting
        3. Global line_length

        Args:
            tool_name: Name of the tool.

        Returns:
            int | None: Effective line length or None.
        """
        tool_config = self.get_tool_config(tool_name)

        # Check tool overrides first
        if "line_length" in tool_config.overrides:
            return tool_config.overrides["line_length"]
        if "line-length" in tool_config.overrides:
            return tool_config.overrides["line-length"]

        # Check tool settings
        if "line_length" in tool_config.settings:
            return tool_config.settings["line_length"]
        if "line-length" in tool_config.settings:
            return tool_config.settings["line-length"]

        # Fall back to global
        return self.global_config.line_length

    def get_effective_target_python(self, tool_name: str) -> str | None:
        """Get effective Python target version for a specific tool.

        Priority:
        1. Tool-specific override
        2. Tool-specific setting
        3. Global target_python

        Args:
            tool_name: Name of the tool.

        Returns:
            str | None: Effective target version or None.
        """
        tool_config = self.get_tool_config(tool_name)

        # Check tool overrides first
        if "target_python" in tool_config.overrides:
            return tool_config.overrides["target_python"]
        if "target-version" in tool_config.overrides:
            return tool_config.overrides["target-version"]

        # Check tool settings
        if "target_python" in tool_config.settings:
            return tool_config.settings["target_python"]
        if "target-version" in tool_config.settings:
            return tool_config.settings["target-version"]

        # Fall back to global
        return self.global_config.target_python
