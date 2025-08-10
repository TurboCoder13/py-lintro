"""Darglint strictness levels."""

from __future__ import annotations

from enum import StrEnum, auto


class DarglintStrictness(StrEnum):
    SHORT = auto()
    LONG = auto()
    FULL = auto()


def normalize_darglint_strictness(
    value: str | DarglintStrictness,
) -> DarglintStrictness:
    if isinstance(value, DarglintStrictness):
        return value
    try:
        return DarglintStrictness[value.upper()]
    except Exception:
        return DarglintStrictness.FULL
