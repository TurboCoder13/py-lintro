"""Boolean string value definitions.

Provides canonical identifiers for boolean string values used in parsing.
"""

from enum import StrEnum, auto


class BooleanString(StrEnum):
    """Supported boolean string value identifiers."""

    TRUE = auto()
    FALSE = auto()
    NONE = auto()
    NULL = auto()
