"""Action/capability enum for tools (check vs. fix)."""

from __future__ import annotations

from enum import StrEnum


class Action(StrEnum):
    """Supported actions a tool can perform."""

    CHECK = "check"
    FIX = "fix"
    TEST = "test"


# Mapping of string aliases to Action enum values
_ACTION_ALIASES: dict[str, Action] = {
    "check": Action.CHECK,
    "fix": Action.FIX,
    "fmt": Action.FIX,
    "format": Action.FIX,
    "test": Action.TEST,
}


def normalize_action(value: str | Action) -> Action:
    """Normalize a raw value to an Action enum.

    Args:
        value: str or Action to normalize. Accepts "check", "fix", "fmt",
            "format", or "test" (case-insensitive).

    Returns:
        Action: Normalized enum value.

    Raises:
        ValueError: If the value is not a recognized action string.

    Examples:
        >>> normalize_action("check")
        <Action.CHECK: 'check'>
        >>> normalize_action("FMT")
        <Action.FIX: 'fix'>
        >>> normalize_action(Action.TEST)
        <Action.TEST: 'test'>
    """
    if isinstance(value, Action):
        return value

    value_lower = value.lower()
    if value_lower in _ACTION_ALIASES:
        return _ACTION_ALIASES[value_lower]

    valid_values = ", ".join(sorted(_ACTION_ALIASES.keys()))
    raise ValueError(
        f"Unknown action: {value!r}. Valid actions are: {valid_values}",
    )
