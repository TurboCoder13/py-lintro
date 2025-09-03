"""Project configuration helpers for Lintro.

Reads configuration from `pyproject.toml` under the `[tool.lintro]` table.
Allows tool-specific defaults via `[tool.lintro.<tool>]` (e.g., `[tool.lintro.ruff]`).
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


def _load_pyproject() -> dict[str, Any]:
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return {}
    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        return data.get("tool", {}).get("lintro", {})
    except Exception:
        return {}


def load_lintro_tool_config(tool_name: str) -> dict[str, Any]:
    """Load tool-specific config from pyproject.

    Args:
        tool_name: Tool name (e.g., "ruff").

    Returns:
        A dict of options for the given tool, or an empty dict if none.
    """
    cfg = _load_pyproject()
    section = cfg.get(tool_name, {})
    if isinstance(section, dict):
        return section
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
