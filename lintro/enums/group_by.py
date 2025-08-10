"""Grouping strategy enum definitions."""

from __future__ import annotations

from enum import StrEnum, auto


class GroupBy(StrEnum):
    """Supported grouping strategies for presenting issues."""

    FILE = auto()
    CODE = auto()
    NONE = auto()
    AUTO = auto()


def normalize_group_by(value: str | GroupBy) -> GroupBy:
    """Normalize a raw value to GroupBy enum.

    Args:
        value: str or GroupBy to normalize.

    Returns:
        GroupBy: Normalized enum value.
    """
    if isinstance(value, GroupBy):
        return value
    try:
        return GroupBy[value.upper()]
    except Exception:
        return GroupBy.FILE
