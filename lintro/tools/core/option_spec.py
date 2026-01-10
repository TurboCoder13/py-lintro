"""Declarative DSL for tool option specifications.

This module provides a type-safe, declarative way to define tool options
with built-in validation and CLI argument generation.

Example usage:
    BLACK_OPTIONS = (
        ToolOptionsSpec()
        .add(int_option("line_length", "--line-length", default=88))
        .add(str_option("target_version", "--target-version"))
        .add(bool_option("preview", "--preview", default=False))
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Generic, TypeVar

from lintro.tools.core.option_validators import (
    validate_bool,
    validate_int,
    validate_list,
    validate_positive_int,
    validate_str,
)

T = TypeVar("T")


class OptionType(Enum):
    """Types of options supported by tool plugins."""

    BOOL = auto()
    INT = auto()
    POSITIVE_INT = auto()
    STR = auto()
    LIST = auto()
    ENUM = auto()


@dataclass
class OptionSpec(Generic[T]):
    """Specification for a single tool option.

    Encapsulates all information needed to validate, store, and convert
    a tool option to CLI arguments.

    Attributes:
        name: The option name as used in Python (e.g., "line_length").
        cli_flag: The CLI flag (e.g., "--line-length").
        option_type: The type of the option value.
        default: Default value if not specified.
        description: Human-readable description.
        min_value: For int types, the minimum allowed value.
        max_value: For int types, the maximum allowed value.
        choices: For enum types, the allowed values.
        required: Whether the option is required.
    """

    name: str
    cli_flag: str
    option_type: OptionType
    default: T | None = None
    description: str = ""
    min_value: int | None = None
    max_value: int | None = None
    choices: list[str] | None = None
    required: bool = False

    def validate(self, value: Any) -> None:
        """Validate a value against this option's specification.

        Args:
            value: The value to validate.

        Raises:
            ValueError: If validation fails.
        """
        if value is None:
            if self.required:
                raise ValueError(f"{self.name} is required")
            return

        if self.option_type == OptionType.BOOL:
            validate_bool(value, self.name)
        elif self.option_type == OptionType.INT:
            validate_int(value, self.name, self.min_value, self.max_value)
        elif self.option_type == OptionType.POSITIVE_INT:
            validate_positive_int(value, self.name)
        elif self.option_type == OptionType.STR:
            validate_str(value, self.name)
            if self.choices and value not in self.choices:
                raise ValueError(
                    f"{self.name} must be one of: {', '.join(self.choices)}",
                )
        elif self.option_type == OptionType.LIST:
            validate_list(value, self.name)
        elif (
            self.option_type == OptionType.ENUM
            and self.choices
            and value not in self.choices
        ):
            raise ValueError(
                f"{self.name} must be one of: {', '.join(self.choices)}",
            )

    def to_cli_args(self, value: Any) -> list[str]:
        """Convert a value to CLI arguments.

        Args:
            value: The value to convert.

        Returns:
            List of CLI arguments (empty if value is None or False for bools).
        """
        if value is None:
            return []

        if self.option_type == OptionType.BOOL:
            # For boolean flags, only include if True
            if value:
                return [self.cli_flag]
            return []

        if self.option_type == OptionType.LIST:
            # For lists, include the flag for each item
            args = []
            for item in value:
                args.extend([self.cli_flag, str(item)])
            return args

        # For all other types, include flag and value
        return [self.cli_flag, str(value)]


@dataclass
class ToolOptionsSpec:
    """Collection of option specifications for a tool.

    Provides methods to add options and validate/convert option values.

    Attributes:
        options: Dictionary mapping option names to their specifications.
    """

    options: dict[str, OptionSpec[Any]] = field(default_factory=dict)

    def add(self, spec: OptionSpec[Any]) -> ToolOptionsSpec:
        """Add an option specification.

        Args:
            spec: The option specification to add.

        Returns:
            Self for method chaining.
        """
        self.options[spec.name] = spec
        return self

    def validate_all(self, values: dict[str, Any]) -> None:
        """Validate all provided values against their specifications.

        Args:
            values: Dictionary of option names to values.

        Raises:
            ValueError: If any validation fails.
        """
        for name, value in values.items():
            if name in self.options:
                self.options[name].validate(value)

        # Check for required options
        for name, spec in self.options.items():
            if spec.required and name not in values:
                raise ValueError(f"{name} is required")

    def to_cli_args(self, values: dict[str, Any]) -> list[str]:
        """Convert all values to CLI arguments.

        Args:
            values: Dictionary of option names to values.

        Returns:
            List of CLI arguments.
        """
        args = []
        for name, value in values.items():
            if name in self.options:
                args.extend(self.options[name].to_cli_args(value))
        return args

    def get_defaults(self) -> dict[str, Any]:
        """Get default values for all options.

        Returns:
            Dictionary of option names to their default values.
        """
        return {
            name: spec.default
            for name, spec in self.options.items()
            if spec.default is not None
        }


# =============================================================================
# Convenience builders
# =============================================================================


def bool_option(
    name: str,
    cli_flag: str,
    default: bool | None = None,
    description: str = "",
) -> OptionSpec[bool]:
    """Create a boolean option specification.

    Args:
        name: The option name.
        cli_flag: The CLI flag.
        default: Default value.
        description: Human-readable description.

    Returns:
        An OptionSpec for a boolean option.

    Example:
        bool_option("preview", "--preview", default=False)
    """
    return OptionSpec(
        name=name,
        cli_flag=cli_flag,
        option_type=OptionType.BOOL,
        default=default,
        description=description,
    )


def int_option(
    name: str,
    cli_flag: str,
    default: int | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
    description: str = "",
) -> OptionSpec[int]:
    """Create an integer option specification.

    Args:
        name: The option name.
        cli_flag: The CLI flag.
        default: Default value.
        min_value: Minimum allowed value.
        max_value: Maximum allowed value.
        description: Human-readable description.

    Returns:
        An OptionSpec for an integer option.

    Example:
        int_option("line_length", "--line-length", default=88, min_value=1)
    """
    return OptionSpec(
        name=name,
        cli_flag=cli_flag,
        option_type=OptionType.INT,
        default=default,
        min_value=min_value,
        max_value=max_value,
        description=description,
    )


def positive_int_option(
    name: str,
    cli_flag: str,
    default: int | None = None,
    description: str = "",
) -> OptionSpec[int]:
    """Create a positive integer option specification.

    Args:
        name: The option name.
        cli_flag: The CLI flag.
        default: Default value (must be positive).
        description: Human-readable description.

    Returns:
        An OptionSpec for a positive integer option.

    Example:
        positive_int_option("timeout", "--timeout", default=30)
    """
    return OptionSpec(
        name=name,
        cli_flag=cli_flag,
        option_type=OptionType.POSITIVE_INT,
        default=default,
        description=description,
    )


def str_option(
    name: str,
    cli_flag: str,
    default: str | None = None,
    choices: list[str] | None = None,
    description: str = "",
) -> OptionSpec[str]:
    """Create a string option specification.

    Args:
        name: The option name.
        cli_flag: The CLI flag.
        default: Default value.
        choices: Allowed values (optional).
        description: Human-readable description.

    Returns:
        An OptionSpec for a string option.

    Example:
        str_option("target_version", "--target-version", choices=["py38", "py39"])
    """
    return OptionSpec(
        name=name,
        cli_flag=cli_flag,
        option_type=OptionType.STR,
        default=default,
        choices=choices,
        description=description,
    )


def list_option(
    name: str,
    cli_flag: str,
    default: list[str] | None = None,
    description: str = "",
) -> OptionSpec[list[str]]:
    """Create a list option specification.

    Args:
        name: The option name.
        cli_flag: The CLI flag.
        default: Default value.
        description: Human-readable description.

    Returns:
        An OptionSpec for a list option.

    Example:
        list_option("ignore", "--ignore", default=["E501"])
    """
    return OptionSpec(
        name=name,
        cli_flag=cli_flag,
        option_type=OptionType.LIST,
        default=default,
        description=description,
    )


def enum_option(
    name: str,
    cli_flag: str,
    choices: list[str],
    default: str | None = None,
    description: str = "",
) -> OptionSpec[str]:
    """Create an enum option specification.

    Args:
        name: The option name.
        cli_flag: The CLI flag.
        choices: Allowed values.
        default: Default value (must be in choices).
        description: Human-readable description.

    Returns:
        An OptionSpec for an enum option.

    Example:
        enum_option("severity", "--severity", choices=["error", "warning", "info"])
    """
    return OptionSpec(
        name=name,
        cli_flag=cli_flag,
        option_type=OptionType.ENUM,
        default=default,
        choices=choices,
        description=description,
    )
