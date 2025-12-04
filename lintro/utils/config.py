"""Project configuration helpers for Lintro.

This module provides backward-compatible access to configuration functions.
The canonical implementation is in unified_config.py.

Reads configuration from `pyproject.toml` under the `[tool.lintro]` table.
Allows tool-specific defaults via `[tool.lintro.<tool>]` (e.g., `[tool.lintro.ruff]`).
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

# Re-export from unified_config for backward compatibility
from lintro.utils.unified_config import (
    get_effective_line_length,
    load_lintro_global_config,
    load_lintro_tool_config,
)
from lintro.utils.unified_config import (
    validate_config_consistency as validate_line_length_consistency,
)


def get_central_line_length() -> int | None:
    """Get the central line length configuration.

    Backward-compatible wrapper that returns the effective line length
    for Ruff (which serves as the source of truth).

    Returns:
        Line length value if configured, None otherwise.
    """
    return get_effective_line_length("ruff")


__all__ = [
    "_load_black_config",
    "_load_pyproject",
    "_load_ruff_config",
    "get_central_line_length",
    "load_lintro_global_config",
    "load_lintro_tool_config",
    "load_post_checks_config",
    "validate_line_length_consistency",
]


def _load_pyproject() -> dict[str, Any]:
    """Load Lintro configuration from pyproject.toml.

    Returns:
        Dict containing [tool.lintro] section or empty dict.
    """
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return {}
    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        return data.get("tool", {}).get("lintro", {})
    except Exception:
        return {}


def _load_ruff_config() -> dict[str, Any]:
    """Load Ruff configuration from pyproject.toml.

    Returns:
        dict[str, Any]: Ruff configuration dictionary from [tool.ruff] section.
    """
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return {}
    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        return data.get("tool", {}).get("ruff", {})
    except Exception:
        return {}


def _load_black_config() -> dict[str, Any]:
    """Load Black configuration from pyproject.toml.

    Returns:
        dict[str, Any]: Black configuration dictionary from [tool.black] section.
    """
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return {}
    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        return data.get("tool", {}).get("black", {})
    except Exception:
        return {}


def load_post_checks_config() -> dict[str, Any]:
    """Load post-checks configuration from pyproject.

    Returns:
        Dict with keys like:
            - enabled: bool
            - tools: list[str]
            - enforce_failure: bool
    """
    cfg = _load_pyproject()
    section = cfg.get("post_checks", {})
    if isinstance(section, dict):
        return section
    return {}
