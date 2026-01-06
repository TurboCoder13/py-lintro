"""Ruff-specific configuration options."""

from dataclasses import dataclass, field

from .base_tool_options import BaseToolOptions


@dataclass
class RuffOptions(BaseToolOptions):
    """Ruff-specific configuration options.

    Attributes:
        select: Rules to enable
        ignore: Rules to ignore
        extend_select: Additional rules to enable
        extend_ignore: Additional rules to ignore
        line_length: Line length limit
        target_version: Python version target
        fix_only: Only apply fixes, don't report remaining issues
        unsafe_fixes: Include unsafe fixes
        show_fixes: Show enumeration of fixes applied
        format: Whether to run `ruff format` during fix
        lint_fix: Whether to run `ruff check --fix` during fix
        format_check: Whether to run `ruff format --check` in check
    """

    select: list[str] | None = field(default=None)
    ignore: list[str] | None = field(default=None)
    extend_select: list[str] | None = field(default=None)
    extend_ignore: list[str] | None = field(default=None)
    line_length: int | None = field(default=None)
    target_version: str | None = field(default=None)
    fix_only: bool | None = field(default=None)
    unsafe_fixes: bool | None = field(default=None)
    show_fixes: bool | None = field(default=None)
    format: bool | None = field(default=None)
    lint_fix: bool | None = field(default=None)
    format_check: bool | None = field(default=None)
