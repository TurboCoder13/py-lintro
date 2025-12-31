"""Environment variable boolean value definitions.

Provides canonical identifiers for boolean environment variable values.
"""

from enum import StrEnum


class EnvBool(StrEnum):
    """Supported boolean environment variable value identifiers."""

    TRUE = "1"
    FALSE = "0"
