"""Darglint strictness levels."""

from __future__ import annotations

from enum import StrEnum, auto


class DarglintStrictness(StrEnum):
    """Strictness levels recognized by Darglint checks."""

    SHORT = auto()
    LONG = auto()
    FULL = auto()


def normalize_darglint_strictness(
    value: str | DarglintStrictness,
) -> DarglintStrictness:
    """Normalize a strictness value, defaulting to FULL on error.

    Args:
        value: String or enum member representing strictness.

    Returns:
        DarglintStrictness: Normalized strictness enum value.
    """
    if isinstance(value, DarglintStrictness):
        return value
    try:
        return DarglintStrictness[value.upper()]
    except Exception:
        return DarglintStrictness.FULL
