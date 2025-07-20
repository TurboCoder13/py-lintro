"""Ruff issue model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RuffIssue:
    """Represents a Ruff linting issue."""

    file: str
    line: int
    column: int
    code: str
    message: str
    url: Optional[str] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    fixable: bool = False
