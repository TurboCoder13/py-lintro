"""Base StrEnum utility classes for custom value generation.

Provides specialized StrEnum subclasses that override value generation
to produce formatted string values when using auto().
"""

from __future__ import annotations

from enum import StrEnum


class UpperCaseStrEnum(StrEnum):
    """StrEnum that generates uppercase string values from member names.

    When using auto(), member names are converted to uppercase strings.
    For example: HEAD = auto() produces 'HEAD'.

    Example:
        class GitRef(UpperCaseStrEnum):
            HEAD = auto()  # value is 'HEAD'
            MAIN = auto()  # value is 'MAIN'
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


class HyphenatedStrEnum(StrEnum):
    """StrEnum that generates lowercase hyphenated string values from member names.

    When using auto(), member names are converted to lowercase strings
    with underscores replaced by hyphens.
    For example: REV_PARSE = auto() produces 'rev-parse'.

    Example:
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
