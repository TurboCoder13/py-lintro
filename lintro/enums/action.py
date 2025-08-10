"""Action/capability enum for tools (check vs. fix)."""

from __future__ import annotations

from enum import StrEnum


class Action(StrEnum):
    """Supported actions a tool can perform."""

    CHECK = "check"
    FIX = "fix"


def normalize_action(value: str | Action) -> Action:
    """Normalize a raw value to an Action enum.

    Args:
        value: str or Action to normalize.

    Returns:
        Action: Normalized enum value.
    """
    if isinstance(value, Action):
        return value
    try:
        return Action(value.lower())
    except Exception:
        return Action.CHECK
