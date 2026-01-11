"""Option validation utilities for tool plugins.

This module provides common validation functions to reduce boilerplate
in tool set_options() methods.
"""

from typing import Any


def validate_bool(value: Any, name: str) -> None:
    """Validate that value is a boolean if not None.

    Args:
        value: Value to validate.
        name: Parameter name for error message.

    Raises:
        ValueError: If value is not None and not a boolean.
    """
    if value is not None and not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")


def validate_str(value: Any, name: str) -> None:
    """Validate that value is a string if not None.

    Args:
        value: Value to validate.
        name: Parameter name for error message.

    Raises:
        ValueError: If value is not None and not a string.
    """
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{name} must be a string")


def validate_int(
    value: Any,
    name: str,
    min_value: int | None = None,
    max_value: int | None = None,
) -> None:
    """Validate that value is an integer if not None.

    Args:
        value: Value to validate.
        name: Parameter name for error message.
        min_value: Optional minimum allowed value (inclusive).
        max_value: Optional maximum allowed value (inclusive).

    Raises:
        ValueError: If value is not None and not an integer, or if value
            is outside the specified range.
    """
    if value is None:
        return

    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")

    if min_value is not None and value < min_value:
        raise ValueError(f"{name} must be at least {min_value}")

    if max_value is not None and value > max_value:
        raise ValueError(f"{name} must be at most {max_value}")


def validate_positive_int(value: Any, name: str) -> None:
    """Validate that value is a positive integer if not None.

    Args:
        value: Value to validate.
        name: Parameter name for error message.

    Raises:
        ValueError: If value is not None and not a positive integer.
    """
    if value is not None:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{name} must be an integer")
        if value <= 0:
            raise ValueError(f"{name} must be positive")


def validate_list(value: Any, name: str) -> None:
    """Validate that value is a list if not None.

    Args:
        value: Value to validate.
        name: Parameter name for error message.

    Raises:
        ValueError: If value is not None and not a list.
    """
    if value is not None and not isinstance(value, list):
        raise ValueError(f"{name} must be a list")


def normalize_str_or_list(value: Any, name: str) -> list[str] | None:
    """Normalize a string or list value to a list.

    Args:
        value: Value to normalize (string, list, or None).
        name: Parameter name for error message.

    Returns:
        List of strings, or None if input was None.

    Raises:
        ValueError: If value is not None, string, or list.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        if not all(isinstance(item, str) for item in value):
            raise ValueError(f"{name} must be a string or list of strings")
        return value
    raise ValueError(f"{name} must be a string or list")


def filter_none_options(**kwargs: Any) -> dict[str, Any]:
    """Filter out None values from keyword arguments.

    Args:
        **kwargs: Keyword arguments to filter.

    Returns:
        Dictionary with only non-None values.
    """
    return {k: v for k, v in kwargs.items() if v is not None}
