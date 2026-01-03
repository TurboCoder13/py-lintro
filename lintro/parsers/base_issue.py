"""Base issue class for all linting tool issues.

This module provides a common base class for all issue types to reduce
duplication across the 14+ different issue dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BaseIssue:
    """Base class for all linting issues.

    Provides common fields that are shared across all issue types.
    Specific issue types should inherit from this class and add their
    own fields as needed.

    Attributes:
        file: File path where the issue was found.
        line: Line number where the issue was found (1-based, 0 means unknown).
        column: Column number where the issue was found (1-based, 0 means unknown).
        message: Human-readable description of the issue.
    """

    file: str = field(default="")
    line: int = field(default=0)
    column: int = field(default=0)
    message: str = field(default="")
