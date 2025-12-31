"""Base tool options dataclass."""

from dataclasses import dataclass, field


@dataclass
class BaseToolOptions:
    """Base class for tool-specific options.

    Attributes:
        timeout: Command execution timeout in seconds
        exclude_patterns: List of glob patterns to exclude
        include_venv: Whether to include virtual environment files
    """

    timeout: int | None = field(default=None)
    exclude_patterns: list[str] | None = field(default=None)
    include_venv: bool | None = field(default=None)
