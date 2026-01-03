"""Git command definitions.

Provides canonical identifiers for git commands used in validation.
"""

from enum import auto

from lintro.enums.hyphenated_str_enum import HyphenatedStrEnum


class GitCommand(HyphenatedStrEnum):
    """Supported git command identifiers."""

    DESCRIBE = auto()
    REV_PARSE = auto()
    LOG = auto()
