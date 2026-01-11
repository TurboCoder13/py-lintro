"""Core formatting abstractions for tool-agnostic table rendering.

Re-exports from format_registry for backward compatibility.
"""

from lintro.formatters.core.format_registry import (
    DEFAULT_FORMAT,
    OutputStyle,
    TableDescriptor,
    get_format_map,
    get_string_format_map,
    get_style,
)

__all__ = [
    "OutputStyle",
    "TableDescriptor",
    "get_style",
    "get_format_map",
    "get_string_format_map",
    "DEFAULT_FORMAT",
]
