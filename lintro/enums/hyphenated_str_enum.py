"""Hyphenated string enumeration types for Lintro.

This module provides the HyphenatedStrEnum class that automatically generates
lowercase hyphenated string values for enum members. Member names should be in
UPPER_CASE with underscores, and the enum value will be a lowercase string with
underscores replaced by hyphens.
"""

from __future__ import annotations

from enum import StrEnum


class HyphenatedStrEnum(StrEnum):
    """StrEnum that generates lowercase hyphenated string values.

    When using auto(), member names are converted to lowercase strings
    with underscores replaced by hyphens.
    For example: REV_PARSE = auto() produces 'rev-parse'.

    Example:
        from enum import auto

        class GitCommand(HyphenatedStrEnum):
            DESCRIBE = auto()  # value is 'describe'
            REV_PARSE = auto()  # value is 'rev-parse'
            LOG = auto()  # value is 'log'
    """

    @staticmethod
    def _generate_next_value_(
        name: str,
        start: int,
        count: int,
        last_values: list[str],
    ) -> str:
        """Generate lowercase hyphenated string value from enum member name.

        Args:
            name: The enum member name.
            start: Starting value (unused).
            count: Number of members processed (unused).
            last_values: Previously generated values (unused).

        Returns:
            str: Lowercase version of the member name with underscores
                replaced by hyphens.
        """
        return name.lower().replace("_", "-")
