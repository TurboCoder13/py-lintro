"""Hadolint enums for formats and failure thresholds."""

from __future__ import annotations

from enum import StrEnum, auto

from loguru import logger


class HadolintFormat(StrEnum):
    """Supported output formats for Hadolint."""

    TTY = auto()
    JSON = auto()
    CHECKSTYLE = auto()
    CODECLIMATE = auto()
    GITLAB_CODECLIMATE = auto()
    GNU = auto()
    CODACY = auto()
    SONARQUBE = auto()
    SARIF = auto()


class HadolintFailureThreshold(StrEnum):
    """Hadolint failure thresholds used to gate exit status."""

    ERROR = auto()
    WARNING = auto()
    INFO = auto()
    STYLE = auto()
    IGNORE = auto()
    NONE = auto()


def normalize_hadolint_format(value: str | HadolintFormat) -> HadolintFormat:
    """Normalize user input to a HadolintFormat.

    Args:
        value: Existing enum member or string name of the format.

    Returns:
        HadolintFormat: Canonical enum value, defaulting to ``TTY`` when
        parsing fails.
    """
    if isinstance(value, HadolintFormat):
        return value
    try:
        return HadolintFormat[value.upper()]
    except (KeyError, AttributeError) as e:
        logger.debug(
            f"Invalid HadolintFormat value '{value}': {e}. Defaulting to TTY.",
        )
        return HadolintFormat.TTY


def normalize_hadolint_threshold(
    value: str | HadolintFailureThreshold,
) -> HadolintFailureThreshold:
    """Normalize user input to a HadolintFailureThreshold.

    Args:
        value: Existing enum member or string name of the threshold.

    Returns:
        HadolintFailureThreshold: Canonical enum value, defaulting to ``INFO``
        when parsing fails.
    """
    if isinstance(value, HadolintFailureThreshold):
        return value
    try:
        return HadolintFailureThreshold[value.upper()]
    except (KeyError, AttributeError) as e:
        logger.debug(
            f"Invalid HadolintFailureThreshold value '{value}': {e}. "
            "Defaulting to INFO.",
        )
        return HadolintFailureThreshold.INFO
