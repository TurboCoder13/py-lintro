"""Bandit severity and confidence level enum definitions.

This module defines the supported severity and confidence levels for Bandit issues.
"""

from __future__ import annotations

from enum import StrEnum, auto


class BanditSeverityLevel(StrEnum):
    """Supported severity levels for Bandit issues.

    Values are upper-case string identifiers to align with Bandit tool outputs.
    """

    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()


class BanditConfidenceLevel(StrEnum):
    """Supported confidence levels for Bandit issues.

    Values are upper-case string identifiers to align with Bandit tool outputs.
    """

    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()


def normalize_bandit_severity_level(
    value: str | BanditSeverityLevel,
) -> BanditSeverityLevel:
    """Normalize a raw value to a BanditSeverityLevel enum.

    Args:
        value: str or BanditSeverityLevel to normalize.

    Returns:
        BanditSeverityLevel: Normalized enum value.

    Raises:
        ValueError: If the value is not a valid severity level.
    """
    if isinstance(value, BanditSeverityLevel):
        return value
    try:
        return BanditSeverityLevel[value.upper()]
    except KeyError as err:
        supported = f"Supported levels: {list(BanditSeverityLevel)}"
        raise ValueError(
            f"Unknown bandit severity level: {value!r}. {supported}",
        ) from err


def normalize_bandit_confidence_level(
    value: str | BanditConfidenceLevel,
) -> BanditConfidenceLevel:
    """Normalize a raw value to a BanditConfidenceLevel enum.

    Args:
        value: str or BanditConfidenceLevel to normalize.

    Returns:
        BanditConfidenceLevel: Normalized enum value.

    Raises:
        ValueError: If the value is not a valid confidence level.
    """
    if isinstance(value, BanditConfidenceLevel):
        return value
    try:
        return BanditConfidenceLevel[value.upper()]
    except KeyError as err:
        raise ValueError(
            f"Unknown bandit confidence level: {value!r}. "
            f"Supported levels: {list(BanditConfidenceLevel)}",
        ) from err
