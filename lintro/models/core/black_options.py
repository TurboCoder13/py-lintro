"""Black-specific configuration options."""

from dataclasses import dataclass, field

from .base_tool_options import BaseToolOptions


@dataclass
class BlackOptions(BaseToolOptions):
    """Black-specific configuration options.

    Attributes:
        line_length: Line length limit
        target_version: Python version target
        skip_string_normalization: Skip string normalization
        skip_magic_trailing_comma: Skip magic trailing comma
    """

    line_length: int | None = field(default=None)
    target_version: str | None = field(default=None)
    skip_string_normalization: bool | None = field(default=None)
    skip_magic_trailing_comma: bool | None = field(default=None)
