"""Module demonstrating various darglint violations.

This module contains functions that intentionally violate darglint rules
to help test the linter's functionality.
"""

from typing import Any


def missing_param_doc(
    param1: str,
    param2: int,
) -> bool:
    """Missing parameter documentation.

    Returns:
        bool: Always returns True.
    """
    return True


def missing_return_doc(
    value: str,
) -> str:
    """Missing return documentation.

    Args:
        value: The input string to process.
    """
    return value.upper()


def inconsistent_param_doc(
    first: str,
    second: int,
) -> tuple[str, int]:
    """Documentation with inconsistent parameter names.

    Args:
        first: The first parameter.
        third: This parameter doesn't exist in the function signature.
        second: The second parameter.

    Returns:
        tuple[str, int]: A tuple containing the processed values.
    """
    return (first, second)


def missing_raises_doc(
    value: Any,
) -> None:
    """Missing raises documentation.

    Args:
        value: The value to check.

    Returns:
        None: This function doesn't return anything.
    """
    if not isinstance(value, (str, int)):
        raise ValueError("Value must be a string or integer")


def incorrect_param_order(
    name: str,
    age: int,
    city: str,
) -> dict[str, Any]:
    """Documentation with parameters in wrong order.

    Args:
        age: The person's age.
        city: The person's city.
        name: The person's name.

    Returns:
        dict[str, Any]: A dictionary containing the person's information.
    """
    return {
        "name": name,
        "age": age,
        "city": city,
    } 