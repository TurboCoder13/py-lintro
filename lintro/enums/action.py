"""Action/capability enum for tools (check vs. fix)."""

from __future__ import annotations

from enum import StrEnum


class Action(StrEnum):
    """Supported actions a tool can perform."""

    CHECK = "check"
    FIX = "fix"
    TEST = "test"


def normalize_action(value: str | Action) -> Action:
    """Normalize a raw value to an Action enum.

    Args:
        value: str or Action to normalize.

    Returns:
        Action: Normalized enum value.
    """
    if isinstance(value, Action):
        return value

    value_lower = value.lower()
    # Handle different string representations
    if value_lower in ("check",):
        return Action.CHECK
    elif value_lower in ("fix", "fmt", "format"):
        return Action.FIX
    elif value_lower in ("test",):
        return Action.TEST
    else:
        return Action.CHECK
