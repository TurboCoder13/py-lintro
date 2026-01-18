"""Semgrep enums for severity levels."""

from __future__ import annotations

from enum import StrEnum, auto


class SemgrepSeverity(StrEnum):
    """Supported severity levels for Semgrep filtering."""

    INFO = auto()
    WARNING = auto()
    ERROR = auto()


def normalize_semgrep_severity(value: str | SemgrepSeverity) -> SemgrepSeverity:
    """Normalize user input to a SemgrepSeverity.

    Args:
        value: Existing enum member or string name of the severity.

    Returns:
        SemgrepSeverity: Canonical enum value.

    Raises:
        ValueError: If the value is not a valid severity level.
    """
    if isinstance(value, SemgrepSeverity):
        return value
    try:
        return SemgrepSeverity[value.upper()]
    except (KeyError, AttributeError) as e:
        valid = ", ".join(s.name for s in SemgrepSeverity)
        raise ValueError(
            f"Invalid Semgrep severity '{value}'. Valid values: {valid}",
        ) from e
