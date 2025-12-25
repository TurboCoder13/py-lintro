"""Typed structure representing a single Prettier issue."""

from dataclasses import dataclass, field

from lintro.parsers.base_issue import BaseIssue


@dataclass
class PrettierIssue(BaseIssue):
    """Simple container for Prettier findings.

    Attributes:
        code: Tool-specific code identifying the rule.
        line: Line number, if provided by Prettier.
        column: Column number, if provided by Prettier.
    """

    code: str = field(default="")
    line: int | None = field(default=None)
    column: int | None = field(default=None)

    def __post_init__(self) -> None:
        """Initialize the inherited fields."""
        # Handle None values for line and column
        if self.line is not None:
            super().__setattr__("line", self.line)
        if self.column is not None:
            super().__setattr__("column", self.column)
