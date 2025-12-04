"""Configuration loader for Lintro.

Loads configuration from .lintro-config.yaml with fallback to
[tool.lintro] in pyproject.toml for backward compatibility.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from loguru import logger

from lintro.config.lintro_config import (
    ExecutionConfig,
    GlobalConfig,
    LintroConfig,
    ToolConfig,
)

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

# Default config file name
LINTRO_CONFIG_FILENAME = ".lintro-config.yaml"
LINTRO_CONFIG_FILENAMES = [
    ".lintro-config.yaml",
    ".lintro-config.yml",
    "lintro-config.yaml",
    "lintro-config.yml",
]


def _find_config_file(start_dir: Path | None = None) -> Path | None:
    """Find .lintro-config.yaml by searching upward from start_dir.

    Args:
        start_dir: Directory to start searching from. Defaults to cwd.

    Returns:
        Path | None: Path to config file if found.
    """
    current = Path(start_dir) if start_dir else Path.cwd()
    current = current.resolve()

    while True:
        for filename in LINTRO_CONFIG_FILENAMES:
            config_path = current / filename
            if config_path.exists():
                return config_path

        # Move up one directory
        parent = current.parent
        if parent == current:
            # Reached filesystem root
            break
        current = parent

    return None


def _load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a YAML file.

    Args:
        path: Path to YAML file.

    Returns:
        dict[str, Any]: Parsed YAML content.

    Raises:
        ImportError: If PyYAML is not installed.
    """
    if yaml is None:
        raise ImportError(
            "PyYAML is required to load .lintro-config.yaml. "
            "Install it with: pip install pyyaml",
        )

    with path.open(encoding="utf-8") as f:
        content = yaml.safe_load(f)

    return content if isinstance(content, dict) else {}


def _load_pyproject_fallback() -> dict[str, Any]:
    """Load [tool.lintro] from pyproject.toml as fallback.

    Returns:
        dict[str, Any]: Lintro configuration from pyproject.toml.
    """
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return {}

    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        return data.get("tool", {}).get("lintro", {})
    except (OSError, tomllib.TOMLDecodeError) as e:
        logger.debug(f"Failed to load pyproject.toml: {e}")
        return {}


def _parse_global_config(data: dict[str, Any]) -> GlobalConfig:
    """Parse global configuration section.

    Args:
        data: Raw 'global' section from config.

    Returns:
        GlobalConfig: Parsed global configuration.
    """
    return GlobalConfig(
        line_length=data.get("line_length"),
        target_python=data.get("target_python"),
        indent_size=data.get("indent_size"),
        quote_style=data.get("quote_style"),
    )


def _parse_execution_config(data: dict[str, Any]) -> ExecutionConfig:
    """Parse execution configuration section.

    Args:
        data: Raw 'execution' section from config.

    Returns:
        ExecutionConfig: Parsed execution configuration.
    """
    enabled_tools = data.get("enabled_tools", [])
    if isinstance(enabled_tools, str):
        enabled_tools = [enabled_tools]

    tool_order = data.get("tool_order", "priority")

    return ExecutionConfig(
        enabled_tools=enabled_tools,
        tool_order=tool_order,
        fail_fast=data.get("fail_fast", False),
        parallel=data.get("parallel", False),
    )


def _parse_tool_config(data: dict[str, Any]) -> ToolConfig:
    """Parse a single tool configuration.

    Args:
        data: Raw tool configuration dict.

    Returns:
        ToolConfig: Parsed tool configuration.
    """
    # Extract known keys
    enabled = data.get("enabled", True)
    config_source = data.get("config_source")
    overrides = data.get("overrides", {})

    # Everything else goes into settings
    settings = {
        k: v
        for k, v in data.items()
        if k not in ("enabled", "config_source", "overrides")
    }

    return ToolConfig(
        enabled=enabled,
        config_source=config_source,
        overrides=overrides if isinstance(overrides, dict) else {},
        settings=settings,
    )


def _parse_tools_config(data: dict[str, Any]) -> dict[str, ToolConfig]:
    """Parse all tool configurations.

    Args:
        data: Raw 'tools' section from config.

    Returns:
        dict[str, ToolConfig]: Tool configurations keyed by tool name.
    """
    tools: dict[str, ToolConfig] = {}

    for tool_name, tool_data in data.items():
        if isinstance(tool_data, dict):
            tools[tool_name.lower()] = _parse_tool_config(tool_data)
        elif isinstance(tool_data, bool):
            # Simple enabled/disabled flag
            tools[tool_name.lower()] = ToolConfig(enabled=tool_data)

    return tools


def _convert_pyproject_to_config(data: dict[str, Any]) -> dict[str, Any]:
    """Convert pyproject.toml [tool.lintro] format to .lintro-config.yaml format.

    The pyproject format uses flat tool sections like [tool.lintro.ruff],
    while .lintro-config.yaml uses nested tools: section.

    Args:
        data: Raw [tool.lintro] section from pyproject.toml.

    Returns:
        dict[str, Any]: Converted configuration in .lintro-config.yaml format.
    """
    result: dict[str, Any] = {
        "global": {},
        "execution": {},
        "tools": {},
    }

    # Known tool names to separate from global settings
    known_tools = {
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
    }

    # Known execution settings
    execution_keys = {"enabled_tools", "tool_order", "fail_fast", "parallel"}

    # Known global settings
    global_keys = {"line_length", "target_python", "indent_size", "quote_style"}

    for key, value in data.items():
        key_lower = key.lower()

        if key_lower in known_tools:
            # Tool-specific config
            result["tools"][key_lower] = value
        elif key in execution_keys or key.replace("-", "_") in execution_keys:
            # Execution config
            result["execution"][key.replace("-", "_")] = value
        elif key in global_keys or key.replace("-", "_") in global_keys:
            # Global config
            result["global"][key.replace("-", "_")] = value
        elif key == "post_checks":
            # Skip post_checks (handled separately)
            pass
        elif key == "versions":
            # Skip versions (handled separately)
            pass
        else:
            # Unknown key - treat as global
            result["global"][key] = value

    return result


def load_config(
    config_path: Path | str | None = None,
    allow_pyproject_fallback: bool = True,
) -> LintroConfig:
    """Load Lintro configuration.

    Priority:
    1. Explicit config_path if provided
    2. .lintro-config.yaml found by searching upward
    3. [tool.lintro] in pyproject.toml (deprecated fallback)
    4. Default empty configuration

    Args:
        config_path: Explicit path to config file. If None, searches for
            .lintro-config.yaml.
        allow_pyproject_fallback: Whether to fall back to pyproject.toml
            if no .lintro-config.yaml is found.

    Returns:
        LintroConfig: Loaded configuration.
    """
    data: dict[str, Any] = {}
    resolved_path: str | None = None

    # Try explicit path first
    if config_path:
        path = Path(config_path)
        if path.exists():
            data = _load_yaml_file(path)
            resolved_path = str(path.resolve())
            logger.debug(f"Loaded config from explicit path: {resolved_path}")
        else:
            logger.warning(f"Config file not found: {config_path}")

    # Try searching for .lintro-config.yaml
    if not data:
        found_path = _find_config_file()
        if found_path:
            data = _load_yaml_file(found_path)
            resolved_path = str(found_path.resolve())
            logger.debug(f"Loaded config from: {resolved_path}")

    # Fall back to pyproject.toml
    if not data and allow_pyproject_fallback:
        pyproject_data = _load_pyproject_fallback()
        if pyproject_data:
            data = _convert_pyproject_to_config(pyproject_data)
            resolved_path = str(Path("pyproject.toml").resolve())
            logger.debug(
                "Using [tool.lintro] from pyproject.toml (deprecated). "
                "Consider migrating to .lintro-config.yaml",
            )

    # Parse configuration sections
    global_config = _parse_global_config(data.get("global", {}))
    execution_config = _parse_execution_config(data.get("execution", {}))
    tools_config = _parse_tools_config(data.get("tools", {}))

    return LintroConfig(
        global_config=global_config,
        execution=execution_config,
        tools=tools_config,
        config_path=resolved_path,
    )


def get_default_config() -> LintroConfig:
    """Get a default configuration with sensible defaults.

    Returns:
        LintroConfig: Default configuration.
    """
    return LintroConfig(
        global_config=GlobalConfig(
            line_length=88,
            target_python="py313",
        ),
        execution=ExecutionConfig(
            tool_order="priority",
        ),
    )


# Global singleton for loaded config
_loaded_config: LintroConfig | None = None


def get_config(reload: bool = False) -> LintroConfig:
    """Get the loaded configuration singleton.

    Args:
        reload: Force reload from disk.

    Returns:
        LintroConfig: Loaded configuration.
    """
    global _loaded_config

    if _loaded_config is None or reload:
        _loaded_config = load_config()

    return _loaded_config


def clear_config_cache() -> None:
    """Clear the configuration cache.

    Useful for testing or when config file has changed.
    """
    global _loaded_config
    _loaded_config = None
