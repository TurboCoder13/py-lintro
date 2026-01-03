"""Tool utilities for handling core operations.

This module provides backward compatibility by re-exporting functions
that have been moved to focused modules.
"""

# Re-exports for backward compatibility
from lintro.utils.output_formatting import TOOL_TABLE_FORMATTERS, format_tool_output
from lintro.utils.path_filtering import (
    should_exclude_path,
    walk_files_with_excludes,
)
from lintro.utils.table_formatting import format_as_table

__all__ = [
    "TOOL_TABLE_FORMATTERS",
    "format_tool_output",
    "VENV_PATTERNS",
    "should_exclude_path",
    "walk_files_with_excludes",
    "format_as_table",
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
