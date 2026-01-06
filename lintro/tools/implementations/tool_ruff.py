"""Ruff Python linter and formatter integration."""

import os
from dataclasses import dataclass, field
from typing import Any

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_config import ToolConfig
from lintro.models.core.tool_result import ToolResult
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.config_utils import load_ruff_config
from lintro.utils.path_utils import load_lintro_ignore

# Constants for Ruff configuration
RUFF_DEFAULT_TIMEOUT: int = 30
RUFF_DEFAULT_PRIORITY: int = 85
RUFF_FILE_PATTERNS: list[str] = ["*.py", "*.pyi"]
RUFF_OUTPUT_FORMAT: str = "json"
RUFF_TEST_MODE_ENV: str = "LINTRO_TEST_MODE"
RUFF_TEST_MODE_VALUE: str = "1"
DEFAULT_REMAINING_ISSUES_DISPLAY: int = 5


@dataclass
class RuffTool(BaseTool):
    """Ruff Python linter and formatter integration.

    Ruff is an extremely fast Python linter and code formatter written in Rust.
    It can replace multiple Python tools like flake8, black, isort, and more.

    Attributes:
        name: str: Tool name.
        description: str: Tool description.
        can_fix: bool: Whether the tool can fix issues.
        config: ToolConfig: Tool configuration.
        exclude_patterns: list[str]: List of patterns to exclude.
        include_venv: bool: Whether to include virtual environment files.
    """

    name: str = "ruff"
    description: str = (
        "Extremely fast Python linter and formatter that replaces multiple tools"
    )
    can_fix: bool = field(default=True)  # Ruff can both check and fix issues
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=RUFF_DEFAULT_PRIORITY,  # High priority, higher than most linters
            conflicts_with=[],  # Can work alongside other tools
            file_patterns=RUFF_FILE_PATTERNS,  # Python files only
            tool_type=ToolType.LINTER | ToolType.FORMATTER,  # Both linter and formatter
            options={
                "timeout": RUFF_DEFAULT_TIMEOUT,  # Default timeout in seconds
                "select": None,  # Rules to enable
                "ignore": None,  # Rules to ignore
                "extend_select": None,  # Additional rules to enable
                "extend_ignore": None,  # Additional rules to ignore
                "line_length": None,  # Line length limit
                "target_version": None,  # Python version target
                "fix_only": False,  # Only apply fixes, don't report remaining issues
                "unsafe_fixes": False,  # Do NOT enable unsafe fixes by default
                "show_fixes": False,  # Show enumeration of fixes applied
                # Wrapper-first defaults:
                # format_check: include `ruff format --check` during check
                # format: run `ruff format` during fix
                # Default True: `lintro chk` runs formatting and lint checks.
                "format_check": True,
                # Default to running the formatter during fmt to apply
                # reformatting along with lint fixes
                "format": True,
                # Allow disabling the lint-fix stage if users only want
                # formatting changes
                "lint_fix": True,
            },
        ),
    )

    def __post_init__(self) -> None:
        """Initialize the tool with default configuration."""
        super().__post_init__()

        # Skip config loading in test mode to allow tests to set specific options
        # without interference from pyproject.toml settings
        if os.environ.get(RUFF_TEST_MODE_ENV) != RUFF_TEST_MODE_VALUE:
            # Load ruff configuration from pyproject.toml
            ruff_config = load_ruff_config()

            # Load .lintro-ignore patterns
            lintro_ignore_patterns = load_lintro_ignore()

            # Update exclude patterns from configuration and .lintro-ignore
            if "exclude" in ruff_config:
                self.exclude_patterns.extend(ruff_config["exclude"])
            if lintro_ignore_patterns:
                self.exclude_patterns.extend(lintro_ignore_patterns)

            # Update other options from configuration
            if "line_length" in ruff_config:
                self.options["line_length"] = ruff_config["line_length"]
            if "target_version" in ruff_config:
                self.options["target_version"] = ruff_config["target_version"]
            if "select" in ruff_config:
                self.options["select"] = ruff_config["select"]
            if "ignore" in ruff_config:
                self.options["ignore"] = ruff_config["ignore"]
            if "unsafe_fixes" in ruff_config:
                self.options["unsafe_fixes"] = ruff_config["unsafe_fixes"]

        # Allow environment variable override for unsafe fixes
        # Useful for development and CI environments
        # This must come after config loading to override config values
        env_unsafe_fixes = os.environ.get("RUFF_UNSAFE_FIXES", "").lower()
        if env_unsafe_fixes in ("true", "1", "yes", "on"):
            self.options["unsafe_fixes"] = True

    def set_options(  # type: ignore[override]
        self,
        select: list[str] | None = None,
        ignore: list[str] | None = None,
        extend_select: list[str] | None = None,
        extend_ignore: list[str] | None = None,
        line_length: int | None = None,
        target_version: str | None = None,
        fix_only: bool | None = None,
        unsafe_fixes: bool | None = None,
        show_fixes: bool | None = None,
        format: bool | None = None,
        lint_fix: bool | None = None,
        format_check: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Set Ruff-specific options.

        Args:
            select: list[str] | None: Rules to enable.
            ignore: list[str] | None: Rules to ignore.
            extend_select: list[str] | None: Additional rules to enable.
            extend_ignore: list[str] | None: Additional rules to ignore.
            line_length: int | None: Line length limit.
            target_version: str | None: Python version target.
            fix_only: bool | None: Only apply fixes, don't report remaining issues.
            unsafe_fixes: bool | None: Include unsafe fixes.
            show_fixes: bool | None: Show enumeration of fixes applied.
            format: bool | None: Whether to run `ruff format` during fix.
            lint_fix: bool | None: Whether to run `ruff check --fix` during fix.
            format_check: bool | None: Whether to run `ruff format --check` in check.
            **kwargs: Other tool options.

        Raises:
            ValueError: If an option value is invalid.
        """
        if select is not None:
            if isinstance(select, str):
                select = [select]
            elif not isinstance(select, list):
                raise ValueError("select must be a string or list of rule codes")
        if ignore is not None:
            if isinstance(ignore, str):
                ignore = [ignore]
            elif not isinstance(ignore, list):
                raise ValueError("ignore must be a string or list of rule codes")
        if extend_select is not None:
            if isinstance(extend_select, str):
                extend_select = [extend_select]
            elif not isinstance(extend_select, list):
                raise ValueError("extend_select must be a string or list of rule codes")
        if extend_ignore is not None:
            if isinstance(extend_ignore, str):
                extend_ignore = [extend_ignore]
            elif not isinstance(extend_ignore, list):
                raise ValueError("extend_ignore must be a string or list of rule codes")
        if line_length is not None:
            if not isinstance(line_length, int):
                raise ValueError("line_length must be an integer")
            if line_length <= 0:
                raise ValueError("line_length must be positive")
        if target_version is not None and not isinstance(target_version, str):
            raise ValueError("target_version must be a string")
        if fix_only is not None and not isinstance(fix_only, bool):
            raise ValueError("fix_only must be a boolean")
        if unsafe_fixes is not None and not isinstance(unsafe_fixes, bool):
            raise ValueError("unsafe_fixes must be a boolean")
        if show_fixes is not None and not isinstance(show_fixes, bool):
            raise ValueError("show_fixes must be a boolean")
        if format is not None and not isinstance(format, bool):
            raise ValueError("format must be a boolean")
        if format_check is not None and not isinstance(format_check, bool):
            raise ValueError("format_check must be a boolean")

        options: dict[str, object] = {
            "select": select,
            "ignore": ignore,
            "extend_select": extend_select,
            "extend_ignore": extend_ignore,
            "line_length": line_length,
            "target_version": target_version,
            "fix_only": fix_only,
            "unsafe_fixes": unsafe_fixes,
            "show_fixes": show_fixes,
            "format": format,
            "lint_fix": lint_fix,
            "format_check": format_check,
        }
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    # Command building moved to lintro.tools.implementations.ruff.commands

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files with Ruff (lint only by default).

        Args:
            paths: list[str]: List of file or directory paths to check.

        Returns:
            ToolResult: ToolResult instance.
        """
        from lintro.tools.implementations.ruff.check import execute_ruff_check

        return execute_ruff_check(self, paths)

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Fix issues in files with Ruff.

        Args:
            paths: list[str]: List of file or directory paths to fix.

        Returns:
            ToolResult: ToolResult instance.
        """
        from lintro.tools.implementations.ruff.fix import execute_ruff_fix

        return execute_ruff_fix(self, paths)
