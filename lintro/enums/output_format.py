"""Output format enum definitions.

This module defines the supported output formats for displaying results.
"""

from __future__ import annotations

from enum import StrEnum, auto


class OutputFormat(StrEnum):
    """Supported output formats for rendering results.

    Values are lower-case string identifiers to align with CLI choices.
    """

    PLAIN = auto()
    GRID = auto()
    MARKDOWN = auto()
    HTML = auto()
    JSON = auto()
    CSV = auto()


def normalize_output_format(value: str | OutputFormat) -> OutputFormat:
    """Normalize a raw value to an OutputFormat enum.

    Args:
        value: str or OutputFormat to normalize.

    Returns:
        OutputFormat: Normalized enum value.
    """
    if isinstance(value, OutputFormat):
        return value
    try:
        return OutputFormat[value.upper()]
    except Exception:
        # Fallback to GRID if invalid; callers may override upstream.
        return OutputFormat.GRID
