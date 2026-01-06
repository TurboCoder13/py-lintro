"""Tool option key definitions.

Provides canonical identifiers for tool option keys used across the codebase.
"""

from enum import StrEnum, auto


class ToolOptionKey(StrEnum):
    """Supported tool option key identifiers."""

    TIMEOUT = auto()
    EXCLUDE_PATTERNS = auto()
    INCLUDE_VENV = auto()
