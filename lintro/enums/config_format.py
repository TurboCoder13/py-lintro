"""Configuration format enum definitions.

This module defines the supported configuration formats.
"""

from __future__ import annotations

from enum import StrEnum, auto


class ConfigFormat(StrEnum):
    """Supported configuration formats.

    Values are lower-case string identifiers to align with CLI choices.
    """

    YAML = auto()
    JSON = auto()


def normalize_config_format(value: str | ConfigFormat) -> ConfigFormat:
    """Normalize a raw value to a ConfigFormat enum.

    Args:
        value: str or ConfigFormat to normalize.

    Returns:
        ConfigFormat: Normalized enum value.

    Raises:
        ValueError: If the value is not a valid config format.
    """
    if isinstance(value, ConfigFormat):
        return value
    try:
        return ConfigFormat[value.upper()]
    except KeyError as err:
        raise ValueError(
            f"Unknown config format: {value!r}. "
            f"Supported formats: {list(ConfigFormat)}",
        ) from err
