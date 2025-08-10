"""Yamllint format enum."""

from __future__ import annotations

from enum import StrEnum, auto


class YamllintFormat(StrEnum):
    PARSABLE = auto()
    STANDARD = auto()
    COLORED = auto()
    GITHUB = auto()
    AUTO = auto()


def normalize_yamllint_format(value: str | YamllintFormat) -> YamllintFormat:
    if isinstance(value, YamllintFormat):
        return value
    try:
        return YamllintFormat[value.upper()]
    except Exception:
        return YamllintFormat.PARSABLE
