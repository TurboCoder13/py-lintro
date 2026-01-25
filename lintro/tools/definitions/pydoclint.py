"""Pydoclint tool definition.

Pydoclint is a Python docstring linter that validates docstrings match
function signatures. It checks for missing, extra, or incorrectly documented
parameters, return values, and raised exceptions.
"""

from __future__ import annotations

import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass
from typing import Any

from lintro.enums.pydoclint_style import (
    PydoclintStyle,
    normalize_pydoclint_style,
)
from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.pydoclint.pydoclint_parser import parse_pydoclint_output
from lintro.plugins.base import BaseToolPlugin
from lintro.plugins.file_processor import FileProcessingResult
from lintro.plugins.protocol import ToolDefinition
from lintro.plugins.registry import register_tool
from lintro.tools.core.option_validators import (
    filter_none_options,
    validate_bool,
    validate_str,
)
from lintro.utils.config import load_pydoclint_config

# Constants for Pydoclint configuration
PYDOCLINT_DEFAULT_TIMEOUT: int = 30
PYDOCLINT_DEFAULT_PRIORITY: int = 45
PYDOCLINT_FILE_PATTERNS: list[str] = ["*.py", "*.pyi"]
PYDOCLINT_DEFAULT_STYLE: str = "google"

# Valid style options for pydoclint
PYDOCLINT_STYLES: tuple[str, ...] = tuple(m.name.lower() for m in PydoclintStyle)


@register_tool
@dataclass
class PydoclintPlugin(BaseToolPlugin):
    """Pydoclint Python docstring linter plugin.

    This plugin integrates pydoclint with Lintro for validating Python
    docstrings match function signatures.
    """

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition.

        Returns:
            ToolDefinition containing tool metadata.
        """
        return ToolDefinition(
            name="pydoclint",
            description=(
                "Python docstring linter that validates docstrings match "
                "function signatures"
            ),
            can_fix=False,
            tool_type=ToolType.LINTER | ToolType.DOCUMENTATION,
            file_patterns=PYDOCLINT_FILE_PATTERNS,
            priority=PYDOCLINT_DEFAULT_PRIORITY,
            conflicts_with=["darglint"],
            native_configs=["pyproject.toml", ".pydoclint.toml"],
            version_command=["pydoclint", "--version"],
            default_options={
                "timeout": PYDOCLINT_DEFAULT_TIMEOUT,
                "style": PYDOCLINT_DEFAULT_STYLE,
                "check_return_types": True,
                "check_arg_order": True,
                "skip_checking_short_docstrings": True,
                "quiet": True,
            },
            default_timeout=PYDOCLINT_DEFAULT_TIMEOUT,
        )

    def __post_init__(self) -> None:
        """Initialize the tool with configuration from pyproject.toml."""
        super().__post_init__()

        # Load pydoclint configuration from pyproject.toml
        pydoclint_config = load_pydoclint_config()

        # Apply timeout from configuration
        if "timeout" in pydoclint_config:
            timeout_value = pydoclint_config["timeout"]
            if isinstance(timeout_value, int) and timeout_value > 0:
                self.options["timeout"] = timeout_value

        # Apply style from configuration
        if "style" in pydoclint_config:
            style_value = pydoclint_config["style"]
            if isinstance(style_value, str):
                self.options["style"] = style_value

    def set_options(  # type: ignore[override]
        self,
        style: str | PydoclintStyle | None = None,
        check_return_types: bool | None = None,
        check_arg_order: bool | None = None,
        skip_checking_short_docstrings: bool | None = None,
        quiet: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Set pydoclint-specific options.

        Args:
            style: Docstring style (google, numpy, sphinx).
            check_return_types: Check return type documentation.
            check_arg_order: Check argument order matches signature.
            skip_checking_short_docstrings: Skip short docstrings.
            quiet: Suppress non-error output.
            **kwargs: Other tool options.
        """
        # Normalize style enum if provided
        if style is not None:
            style_enum = normalize_pydoclint_style(style)
            style = style_enum.name.lower()

        validate_str(style, "style")
        validate_bool(check_return_types, "check_return_types")
        validate_bool(check_arg_order, "check_arg_order")
        validate_bool(skip_checking_short_docstrings, "skip_checking_short_docstrings")
        validate_bool(quiet, "quiet")

        options = filter_none_options(
            style=style,
            check_return_types=check_return_types,
            check_arg_order=check_arg_order,
            skip_checking_short_docstrings=skip_checking_short_docstrings,
            quiet=quiet,
        )
        super().set_options(**options, **kwargs)

    def _build_command(self) -> list[str]:
        """Build the pydoclint command.

        Returns:
            List of command arguments.
        """
        cmd: list[str] = ["pydoclint"]

        # Add style option
        style = str(self.options.get("style") or PYDOCLINT_DEFAULT_STYLE)
        cmd.extend(["--style", style])

        # Add boolean options (pydoclint uses --option BOOLEAN format with lowercase)
        check_return_types = self.options.get("check_return_types", True)
        cmd.extend(["--check-return-types", str(check_return_types).lower()])

        check_arg_order = self.options.get("check_arg_order", True)
        cmd.extend(["--check-arg-order", str(check_arg_order).lower()])

        skip_short = self.options.get("skip_checking_short_docstrings", True)
        cmd.extend(["--skip-checking-short-docstrings", str(skip_short).lower()])

        quiet = self.options.get("quiet", True)
        if quiet:
            cmd.append("--quiet")

        return cmd

    def _process_single_file(
        self,
        file_path: str,
        timeout: int,
    ) -> FileProcessingResult:
        """Process a single Python file with pydoclint.

        Args:
            file_path: Path to the Python file to process.
            timeout: Timeout in seconds for the pydoclint command.

        Returns:
            FileProcessingResult with processing outcome.
        """
        cmd = self._build_command() + [str(file_path)]
        try:
            success, output = self._run_subprocess(cmd=cmd, timeout=timeout)
            issues = parse_pydoclint_output(output=output)
            return FileProcessingResult(
                success=success and len(issues) == 0,
                output=output,
                issues=issues,
            )
        except subprocess.TimeoutExpired:
            return FileProcessingResult(
                success=False,
                output="",
                issues=[],
                skipped=True,
            )
        except (OSError, ValueError, RuntimeError) as e:
            return FileProcessingResult(
                success=False,
                output="",
                issues=[],
                error=str(e),
            )

    def check(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Check files with pydoclint.

        Args:
            paths: List of file or directory paths to check.
            options: Runtime options that override defaults.

        Returns:
            ToolResult with check results.
        """
        ctx = self._prepare_execution(paths=paths, options=options)
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        result = self._process_files_with_progress(
            files=ctx.files,
            processor=lambda f: self._process_single_file(f, ctx.timeout),
            timeout=ctx.timeout,
        )

        return ToolResult(
            name=self.definition.name,
            success=result.all_success and result.total_issues == 0,
            output=result.build_output(timeout=ctx.timeout),
            issues_count=result.total_issues,
            issues=result.all_issues,
        )

    def fix(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Pydoclint cannot fix issues, only report them.

        Args:
            paths: List of file or directory paths to fix.
            options: Tool-specific options.

        Raises:
            NotImplementedError: Pydoclint does not support fixing issues.
        """
        raise NotImplementedError(
            "Pydoclint cannot automatically fix issues. Run 'lintro check' to see "
            "issues.",
        )
