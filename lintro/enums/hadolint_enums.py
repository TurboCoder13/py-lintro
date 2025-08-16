"""Hadolint enums for formats and failure thresholds."""

from __future__ import annotations

from enum import StrEnum, auto


class HadolintFormat(StrEnum):
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
    ERROR = auto()
    WARNING = auto()
    INFO = auto()
    STYLE = auto()
    IGNORE = auto()
    NONE = auto()


def normalize_hadolint_format(value: str | HadolintFormat) -> HadolintFormat:
    if isinstance(value, HadolintFormat):
        return value
    try:
        return HadolintFormat[value.upper()]
    except Exception:
        return HadolintFormat.TTY


def normalize_hadolint_threshold(
    value: str | HadolintFailureThreshold,
) -> HadolintFailureThreshold:
    if isinstance(value, HadolintFailureThreshold):
        return value
    try:
        return HadolintFailureThreshold[value.upper()]
    except Exception:
        return HadolintFailureThreshold.INFO
