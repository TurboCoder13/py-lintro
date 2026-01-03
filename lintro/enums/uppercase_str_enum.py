"""Uppercase string enumeration types for Lintro.

This module provides the UppercaseStrEnum class that automatically generates
uppercase string values for enum members. Member names should be in UPPER_CASE
and the enum value will be an uppercase string of the member name.
"""

from __future__ import annotations

from enum import StrEnum


class UppercaseStrEnum(StrEnum):
    """StrEnum that generates uppercase string values.

    When using auto(), member names are converted to uppercase strings.
    For example: HEAD = auto() produces 'HEAD'.

    Example:
        from enum import auto

        class MyEnum(UppercaseStrEnum):
            LOW = auto()  # value is 'LOW'
            HIGH = auto()  # value is 'HIGH'
    """

    @staticmethod
    def _generate_next_value_(
        name: str,
        start: int,
        count: int,
        last_values: list[str],
    ) -> str:
        """Generate uppercase string value from enum member name.

        Args:
            name: The enum member name.
            start: Starting value (unused).
            count: Number of members processed (unused).
            last_values: Previously generated values (unused).

        Returns:
            str: Uppercase version of the member name.
        """
        return name.upper()
