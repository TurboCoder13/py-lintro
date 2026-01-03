"""Git reference definitions.

Provides canonical identifiers for git references used in validation.
"""

from enum import auto

from lintro.enums.uppercase_str_enum import UppercaseStrEnum


class GitRef(UppercaseStrEnum):
    """Supported git reference identifiers."""

    HEAD = auto()
