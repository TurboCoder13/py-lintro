"""Yamllint-specific configuration options."""

from dataclasses import dataclass, field

from .base_tool_options import BaseToolOptions


@dataclass
class YamllintOptions(BaseToolOptions):
    """Yamllint-specific configuration options.

    Attributes:
        config_file: Path to config file
        strict: Strict mode
    """

    config_file: str | None = field(default=None)
    strict: bool | None = field(default=None)
