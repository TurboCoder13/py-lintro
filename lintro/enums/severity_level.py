"""Severity level enum definitions.

This module defines the supported severity levels for issues.
"""

from __future__ import annotations

from enum import auto

from lintro.enums.uppercase_str_enum import UppercaseStrEnum


class SeverityLevel(UppercaseStrEnum):
    """Supported severity levels for issues.

    Values are uppercase string identifiers matching enum member names.
    """

    ERROR = auto()
    WARNING = auto()
    INFO = auto()


def normalize_severity_level(value: str | SeverityLevel) -> SeverityLevel:
    """Normalize a raw value to a SeverityLevel enum.

    Args:
        value: str or SeverityLevel to normalize.

    Returns:
        SeverityLevel: Normalized enum value.

    Raises:
        ValueError: If the value is not a valid severity level.
    """
    if isinstance(value, SeverityLevel):
        return value
    try:
        return SeverityLevel[value.upper()]
    except KeyError as err:
        supported = f"Supported levels: {list(SeverityLevel)}"
        raise ValueError(
            f"Unknown severity level: {value!r}. {supported}",
        ) from err
