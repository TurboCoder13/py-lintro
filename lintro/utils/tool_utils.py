"""Tool utilities for handling core operations.

This module provides backward compatibility by re-exporting functions
that have been moved to focused modules.
"""

# Re-exports for backward compatibility
from lintro.utils.output import format_tool_output
from lintro.utils.path_filtering import (
    should_exclude_path,
    walk_files_with_excludes,
)

__all__ = [
    "format_tool_output",
    "VENV_PATTERNS",
    "should_exclude_path",
    "walk_files_with_excludes",
]

# Legacy constants (kept for backward compatibility)
VENV_PATTERNS: list[str] = [
    "venv",
    "env",
    "ENV",
    ".venv",
    ".env",
    "virtualenv",
    "virtual_env",
    "virtualenvs",
    "site-packages",
    "node_modules",
]
