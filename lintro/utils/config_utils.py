"""Utilities for loading tool configurations from various sources.

This module provides centralized functions for loading configuration data
from pyproject.toml and other config files, reducing duplication across
different tool implementations.
"""

import configparser
import tomllib
from pathlib import Path
from typing import Any

from loguru import logger


def load_pyproject_config() -> dict[str, Any]:
    """Load the entire pyproject.toml configuration.

    Returns:
        dict[str, Any]: Complete pyproject.toml configuration, or empty dict if
        not found.
    """
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return {}

    try:
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        logger.warning(f"Failed to load pyproject.toml: {e}")
        return {}


def load_tool_config_from_pyproject(tool_name: str) -> dict[str, Any]:
    """Load tool-specific configuration from pyproject.toml.

    Args:
        tool_name: Name of the tool to load config for.

    Returns:
        dict[str, Any]: Tool configuration dictionary, or empty dict if not found.
    """
    pyproject_data = load_pyproject_config()
    tool_section = pyproject_data.get("tool", {})

    if tool_name in tool_section:
        config = tool_section[tool_name]
        if isinstance(config, dict):
            return config

    return {}


def load_ruff_config() -> dict[str, Any]:
    """Load ruff configuration from pyproject.toml with flattened lint settings.

    Returns:
        dict[str, Any]: Ruff configuration dictionary with flattened lint settings.
    """
    config = load_tool_config_from_pyproject("ruff")

    # Flatten nested lint section to top level for easy access
    if "lint" in config:
        lint_config = config["lint"]
        if isinstance(lint_config, dict):
            if "select" in lint_config:
                config["select"] = lint_config["select"]
            if "ignore" in lint_config:
                config["ignore"] = lint_config["ignore"]
            if "extend-select" in lint_config:
                config["extend_select"] = lint_config["extend-select"]
            if "extend-ignore" in lint_config:
                config["extend_ignore"] = lint_config["extend-ignore"]

    return config


def load_bandit_config() -> dict[str, Any]:
    """Load bandit configuration from pyproject.toml.

    Returns:
        dict[str, Any]: Bandit configuration dictionary.
    """
    return load_tool_config_from_pyproject("bandit")


def load_black_config() -> dict[str, Any]:
    """Load black configuration from pyproject.toml.

    Returns:
        dict[str, Any]: Black configuration dictionary.
    """
    return load_tool_config_from_pyproject("black")


def load_mypy_config(
    base_dir: Path | None = None,
) -> tuple[dict[str, Any], Path | None]:
    """Load mypy configuration from pyproject.toml or mypy.ini files.

    Args:
        base_dir: Directory to search for mypy configuration files.
            Defaults to the current working directory.

    Returns:
        tuple[dict[str, Any], Path | None]: Parsed configuration data and the
            path to the config file if found.
    """
    root = base_dir or Path.cwd()

    # Try pyproject.toml first
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            with pyproject.open("rb") as handle:
                data = tomllib.load(handle)
            pyproject_config = data.get("tool", {}).get("mypy", {}) or {}
            if pyproject_config:
                return pyproject_config, pyproject
        except Exception as e:
            logger.warning(f"Failed to load mypy config from pyproject.toml: {e}")

    # Fallback to mypy.ini or .mypy.ini
    for config_file in [".mypy.ini", "mypy.ini"]:
        config_path = root / config_file
        if config_path.exists():
            try:
                parser = configparser.ConfigParser()
                parser.read(config_path)
                if "mypy" in parser:
                    config_dict = dict(parser["mypy"])
                    return config_dict, config_path
            except Exception as e:
                logger.warning(f"Failed to load mypy config from {config_file}: {e}")

    return {}, None
