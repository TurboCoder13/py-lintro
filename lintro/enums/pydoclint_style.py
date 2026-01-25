"""Pydoclint docstring style options."""

from __future__ import annotations

from enum import StrEnum, auto

from loguru import logger


class PydoclintStyle(StrEnum):
    """Docstring style formats recognized by pydoclint."""

    GOOGLE = auto()
    NUMPY = auto()
    SPHINX = auto()


def normalize_pydoclint_style(
    value: str | PydoclintStyle,
) -> PydoclintStyle:
    """Normalize a style value, defaulting to GOOGLE on error.

    Args:
        value: String or enum member representing style.

    Returns:
        PydoclintStyle: Normalized style enum value.
    """
    if isinstance(value, PydoclintStyle):
        return value
    try:
        return PydoclintStyle[value.upper()]
    except (KeyError, AttributeError) as e:
        logger.debug(
            f"Invalid PydoclintStyle value '{value}': {e}. Defaulting to GOOGLE.",
        )
        return PydoclintStyle.GOOGLE
