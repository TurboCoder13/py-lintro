"""Tool configuration generator for Lintro.

Generates temporary configuration files for each tool based on
the unified Lintro configuration. This ensures tools receive
only Lintro-managed configuration, ignoring native config files.
"""

from __future__ import annotations

import atexit
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from loguru import logger

from lintro.config.lintro_config import LintroConfig, ToolConfig

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

try:
    import toml
except ImportError:
    toml = None  # type: ignore[assignment]


# Global setting mappings: lintro key -> {tool: tool_key}
GLOBAL_SETTING_MAPPINGS: dict[str, dict[str, str]] = {
    "line_length": {
        "ruff": "line-length",
        "black": "line-length",
        "prettier": "printWidth",
        "yamllint": "line-length",  # nested under rules.line-length.max
        "markdownlint": "line_length",  # MD013 rule
    },
    "target_python": {
        "ruff": "target-version",
        "black": "target-version",
    },
}

# Tool config format: what format does each tool expect?
TOOL_CONFIG_FORMATS: dict[str, str] = {
    "ruff": "toml",
    "black": "toml",
    "prettier": "json",
    "yamllint": "yaml",
    "markdownlint": "json",
    "hadolint": "yaml",
    "bandit": "yaml",
    "actionlint": "yaml",
}

# Track temporary files for cleanup
_temp_files: list[Path] = []


def _cleanup_temp_files() -> None:
    """Clean up temporary config files on exit."""
    for temp_file in _temp_files:
        try:
            if temp_file.exists():
                temp_file.unlink()
                logger.debug(f"Cleaned up temp config: {temp_file}")
        except Exception as e:
            logger.debug(f"Failed to clean up {temp_file}: {e}")


# Register cleanup on exit
atexit.register(_cleanup_temp_files)


def _load_config_source(
    config_source: str,
    tool_name: str,
) -> dict[str, Any]:
    """Load a native config file as base configuration.

    Args:
        config_source: Path to native config file.
        tool_name: Name of the tool (for format detection).

    Returns:
        dict[str, Any]: Parsed configuration.
    """
    path = Path(config_source)
    if not path.exists():
        logger.warning(f"Config source not found: {config_source}")
        return {}

    suffix = path.suffix.lower()
    content = path.read_text(encoding="utf-8")

    try:
        if suffix in (".json", ".jsonc"):
            # Handle JSONC (JSON with comments)
            from lintro.utils.unified_config import _strip_jsonc_comments

            content = _strip_jsonc_comments(content)
            return json.loads(content)

        elif suffix in (".yaml", ".yml"):
            if yaml is None:
                logger.warning("PyYAML not installed, cannot load YAML config")
                return {}
            result = yaml.safe_load(content)
            return result if isinstance(result, dict) else {}

        elif suffix == ".toml":
            if toml is None:
                logger.warning("toml package not installed, cannot load TOML config")
                return {}
            return toml.loads(content)

        else:
            # Try JSON first, then YAML
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                if yaml:
                    result = yaml.safe_load(content)
                    return result if isinstance(result, dict) else {}
                return {}

    except Exception as e:
        logger.warning(f"Failed to parse {config_source}: {e}")
        return {}


def _apply_global_settings(
    config: dict[str, Any],
    lintro_config: LintroConfig,
    tool_name: str,
) -> dict[str, Any]:
    """Apply global Lintro settings to tool config.

    Maps global settings like line_length to tool-specific keys.

    Args:
        config: Current tool configuration.
        lintro_config: Lintro configuration.
        tool_name: Name of the tool.

    Returns:
        dict[str, Any]: Updated configuration.
    """
    result = dict(config)
    tool_lower = tool_name.lower()

    # Apply line_length mapping
    if tool_lower in GLOBAL_SETTING_MAPPINGS.get("line_length", {}):
        line_length = lintro_config.get_effective_line_length(tool_name)
        if line_length is not None:
            tool_key = GLOBAL_SETTING_MAPPINGS["line_length"][tool_lower]

            # Special handling for yamllint (nested structure)
            if tool_lower == "yamllint":
                if "rules" not in result:
                    result["rules"] = {}
                if "line-length" not in result["rules"]:
                    result["rules"]["line-length"] = {}
                result["rules"]["line-length"]["max"] = line_length

            # Special handling for markdownlint (MD013 rule)
            elif tool_lower == "markdownlint":
                if "MD013" not in result:
                    result["MD013"] = {}
                result["MD013"]["line_length"] = line_length
                result["MD013"]["code_blocks"] = False
                result["MD013"]["tables"] = False

            else:
                result[tool_key] = line_length

    # Apply target_python mapping
    if tool_lower in GLOBAL_SETTING_MAPPINGS.get("target_python", {}):
        target_python = lintro_config.get_effective_target_python(tool_name)
        if target_python is not None:
            tool_key = GLOBAL_SETTING_MAPPINGS["target_python"][tool_lower]
            result[tool_key] = target_python

    return result


def _deep_merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two dictionaries.

    Values from override take precedence. Nested dictionaries are merged
    recursively rather than replaced.

    Args:
        base: Base dictionary to merge into.
        override: Dictionary with values to override base.

    Returns:
        dict[str, Any]: Deeply merged dictionary.
    """
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def _merge_tool_settings(
    base_config: dict[str, Any],
    tool_config: ToolConfig,
) -> dict[str, Any]:
    """Merge tool-specific settings and overrides into base config.

    Performs a recursive deep merge for nested dictionaries, preserving
    keys from both sides and overriding scalars from the override dict.

    Args:
        base_config: Base configuration (from config_source or empty).
        tool_config: Lintro tool configuration.

    Returns:
        dict[str, Any]: Merged configuration.
    """
    result = dict(base_config)

    # Apply settings (lower priority)
    for key, value in tool_config.settings.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            # Recursive deep merge for nested dicts
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    # Apply overrides (highest priority)
    for key, value in tool_config.overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            # Recursive deep merge for nested dicts
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def _write_config_file(
    config: dict[str, Any],
    tool_name: str,
    config_format: str | None = None,
) -> Path:
    """Write configuration to a temporary file.

    Args:
        config: Configuration dictionary.
        tool_name: Name of the tool.
        config_format: Output format (toml, json, yaml). Auto-detected if None.

    Returns:
        Path: Path to temporary config file.

    Raises:
        ImportError: If required package (toml/PyYAML) is not installed.
    """
    fmt = config_format or TOOL_CONFIG_FORMATS.get(tool_name.lower(), "json")

    # Determine file suffix
    suffix_map = {"toml": ".toml", "json": ".json", "yaml": ".yaml"}
    suffix = suffix_map.get(fmt, ".json")

    # Special handling for markdownlint-cli2 which requires specific filename
    if tool_name.lower() == "markdownlint":
        # markdownlint-cli2 requires files named like .markdownlint-cli2.jsonc
        temp_fd, temp_path_str = tempfile.mkstemp(
            prefix="lintro-",
            suffix=".markdownlint-cli2.jsonc",
        )
    else:
        # Create temporary file with standard naming
        temp_fd, temp_path_str = tempfile.mkstemp(
            prefix=f"lintro-{tool_name}-",
            suffix=suffix,
        )
    # Close the file descriptor immediately - we'll write via Path.write_text
    os.close(temp_fd)
    temp_path = Path(temp_path_str)
    _temp_files.append(temp_path)

    # Write content
    try:
        if fmt == "toml":
            if toml is None:
                raise ImportError("toml package required for TOML output")
            content = toml.dumps(config)

        elif fmt == "yaml":
            if yaml is None:
                raise ImportError("PyYAML required for YAML output")
            content = yaml.dump(config, default_flow_style=False)

        else:  # json
            content = json.dumps(config, indent=2)

        temp_path.write_text(content, encoding="utf-8")
        logger.debug(f"Generated temp config for {tool_name}: {temp_path}")

        return temp_path

    except Exception as e:
        logger.error(f"Failed to write config for {tool_name}: {e}")
        raise


def generate_tool_config(
    tool_name: str,
    lintro_config: LintroConfig,
) -> Path | None:
    """Generate a temporary configuration file for a tool.

    This is the main entry point for generating tool configs.
    It:
    1. Loads config_source if specified
    2. Merges with tool settings from Lintro config
    3. Applies overrides
    4. Maps global settings
    5. Writes to a temp file

    Args:
        tool_name: Name of the tool (e.g., "ruff", "prettier").
        lintro_config: Lintro configuration.

    Returns:
        Path | None: Path to generated config file, or None if generation fails.
    """
    tool_lower = tool_name.lower()
    tool_config = lintro_config.get_tool_config(tool_lower)

    # Start with config_source or empty dict
    base_config: dict[str, Any] = {}
    if tool_config.config_source:
        base_config = _load_config_source(
            config_source=tool_config.config_source,
            tool_name=tool_lower,
        )
        logger.debug(
            f"Loaded config_source for {tool_name}: {tool_config.config_source}",
        )

    # Merge tool settings
    merged_config = _merge_tool_settings(
        base_config=base_config,
        tool_config=tool_config,
    )

    # Apply global settings mappings
    final_config = _apply_global_settings(
        config=merged_config,
        lintro_config=lintro_config,
        tool_name=tool_lower,
    )

    # If config is empty, don't generate a file
    if not final_config:
        return None

    try:
        return _write_config_file(
            config=final_config,
            tool_name=tool_lower,
        )
    except Exception as e:
        logger.error(f"Failed to generate config for {tool_name}: {e}")
        return None


def get_config_injection_args(
    tool_name: str,
    config_path: Path | None,
) -> list[str]:
    """Get CLI arguments to inject config file into a tool.

    Args:
        tool_name: Name of the tool.
        config_path: Path to config file (or None).

    Returns:
        list[str]: CLI arguments to pass to the tool.
    """
    if config_path is None:
        return []

    tool_lower = tool_name.lower()
    config_str = str(config_path)

    # Tool-specific config flags
    config_flags: dict[str, list[str]] = {
        "ruff": ["--config", config_str],
        "black": ["--config", config_str],
        "prettier": ["--config", config_str],
        "yamllint": ["-c", config_str],
        "markdownlint": ["--config", config_str],
        "hadolint": ["--config", config_str],
        "bandit": ["-c", config_str],
        "actionlint": ["-config-file", config_str],
    }

    return config_flags.get(tool_lower, [])


def get_no_auto_config_args(tool_name: str) -> list[str]:
    """Get CLI arguments to disable auto-config discovery.

    Some tools support flags to prevent auto-discovery of native configs.

    Args:
        tool_name: Name of the tool.

    Returns:
        list[str]: CLI arguments to disable auto-config.
    """
    tool_lower = tool_name.lower()

    # Tool-specific no-auto-config flags
    # Note: Prettier doesn't need --no-config when --config is passed
    # (and actually errors if both are used together)
    no_auto_flags: dict[str, list[str]] = {
        "ruff": ["--isolated"],
    }

    return no_auto_flags.get(tool_lower, [])


def cleanup_temp_config(config_path: Path) -> None:
    """Explicitly clean up a temporary config file.

    Args:
        config_path: Path to temporary config file.
    """
    try:
        if config_path in _temp_files:
            _temp_files.remove(config_path)
        if config_path.exists():
            config_path.unlink()
            logger.debug(f"Cleaned up temp config: {config_path}")
    except Exception as e:
        logger.debug(f"Failed to clean up {config_path}: {e}")
