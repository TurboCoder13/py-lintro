"""Git reference definitions.

Provides canonical identifiers for git references used in validation.
"""

from enum import auto

from lintro.enums.base import UpperCaseStrEnum


class GitRef(UpperCaseStrEnum):
    """Supported git reference identifiers."""

    HEAD = auto()
