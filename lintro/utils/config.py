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

from loguru import logger

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
    "get_central_line_length",
    "load_lintro_global_config",
    "load_lintro_tool_config",
    "load_post_checks_config",
    "validate_line_length_consistency",
]


def _load_lintro_section() -> dict[str, Any]:
    """Load Lintro configuration section from pyproject.toml.

    Returns:
        Dict containing [tool.lintro] section or empty dict.
    """
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return {}
    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        tool_section = data.get("tool", {})
        lintro_section = (
            tool_section.get("lintro", {}) if isinstance(tool_section, dict) else {}
        )
        return lintro_section if isinstance(lintro_section, dict) else {}
    except Exception as e:
        logger.debug(f"Failed to load Lintro configuration from pyproject.toml: {e}")
        return {}


def load_post_checks_config() -> dict[str, Any]:
    """Load post-checks configuration from pyproject.

    Returns:
        Dict with keys like:
            - enabled: bool
            - tools: list[str]
            - enforce_failure: bool
    """
    cfg = _load_lintro_section()
    section = cfg.get("post_checks", {})
    if isinstance(section, dict):
        return section
    return {}
