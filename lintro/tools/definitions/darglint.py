"""Darglint tool definition.

Darglint is a Python docstring linter that checks docstring style and completeness.
It verifies that docstrings match the function signature and contain all required
sections.
"""

from __future__ import annotations

import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass
from typing import Any

import click

from lintro.enums.darglint_strictness import (
    DarglintStrictness,
    normalize_darglint_strictness,
)
from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.darglint.darglint_issue import DarglintIssue
from lintro.parsers.darglint.darglint_parser import parse_darglint_output
from lintro.plugins.base import BaseToolPlugin
from lintro.plugins.protocol import ToolDefinition
from lintro.plugins.registry import register_tool
from lintro.tools.core.option_validators import (
    filter_none_options,
    validate_bool,
    validate_int,
    validate_list,
    validate_str,
)
from lintro.utils.config import load_darglint_config

# Constants for Darglint configuration
DARGLINT_DEFAULT_TIMEOUT: int = 15
DARGLINT_DEFAULT_PRIORITY: int = 45
DARGLINT_FILE_PATTERNS: list[str] = ["*.py"]
DARGLINT_STRICTNESS_LEVELS: tuple[str, ...] = tuple(
    m.name.lower() for m in DarglintStrictness
)
DARGLINT_MIN_VERBOSITY: int = 1
DARGLINT_MAX_VERBOSITY: int = 3
DARGLINT_DEFAULT_VERBOSITY: int = 2
DARGLINT_DEFAULT_STRICTNESS: str = "full"


@dataclass
class FileProcessResult:
    """Result of processing a single file with Darglint.

    Attributes:
        success: Whether the file was processed successfully.
        issues_count: Number of issues found.
        issues: List of parsed issues.
        output: Raw output from the tool, or None if no output.
        timeout_issue: Timeout issue if a timeout occurred, or None.
    """

    success: bool
    issues_count: int
    issues: list[DarglintIssue]
    output: str | None
    timeout_issue: DarglintIssue | None


@register_tool
@dataclass
class DarglintPlugin(BaseToolPlugin):
    """Darglint Python docstring linter plugin.

    This plugin integrates Darglint with Lintro for checking Python
    docstrings for style and completeness.
    """

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition.

        Returns:
            ToolDefinition containing tool metadata.
        """
        return ToolDefinition(
            name="darglint",
            description=(
                "Python docstring linter that checks docstring style and completeness"
            ),
            can_fix=False,
            tool_type=ToolType.LINTER,
            file_patterns=DARGLINT_FILE_PATTERNS,
            priority=DARGLINT_DEFAULT_PRIORITY,
            conflicts_with=[],
            native_configs=[".darglint", "setup.cfg", "tox.ini"],
            version_command=["darglint", "--version"],
            min_version="1.8.0",
            default_options={
                "timeout": DARGLINT_DEFAULT_TIMEOUT,
                "ignore": None,
                "ignore_regex": None,
                "ignore_syntax": False,
                "message_template": None,
                "verbosity": DARGLINT_DEFAULT_VERBOSITY,
                "strictness": DARGLINT_DEFAULT_STRICTNESS,
            },
            default_timeout=DARGLINT_DEFAULT_TIMEOUT,
        )

    def __post_init__(self) -> None:
        """Initialize the tool with configuration from pyproject.toml."""
        super().__post_init__()

        # Load darglint configuration from pyproject.toml
        darglint_config = load_darglint_config()

        # Apply exclude_dirs as exclude patterns
        if "exclude_dirs" in darglint_config:
            exclude_dirs = darglint_config["exclude_dirs"]
            if isinstance(exclude_dirs, list):
                for exclude_dir in exclude_dirs:
                    pattern = f"{exclude_dir}/*"
                    if pattern not in self.exclude_patterns:
                        self.exclude_patterns.append(pattern)

        # Apply timeout from configuration
        if "timeout" in darglint_config:
            timeout_value = darglint_config["timeout"]
            if isinstance(timeout_value, int) and timeout_value > 0:
                self.options["timeout"] = timeout_value

        # Apply exclude_files as exclude patterns
        if "exclude_files" in darglint_config:
            exclude_files = darglint_config["exclude_files"]
            if isinstance(exclude_files, list):
                for exclude_file in exclude_files:
                    if exclude_file not in self.exclude_patterns:
                        self.exclude_patterns.append(exclude_file)

    def set_options(  # type: ignore[override]
        self,
        ignore: list[str] | None = None,
        ignore_regex: str | None = None,
        ignore_syntax: bool | None = None,
        message_template: str | None = None,
        verbosity: int | None = None,
        strictness: str | DarglintStrictness | None = None,
        **kwargs: Any,
    ) -> None:
        """Set Darglint-specific options.

        Args:
            ignore: List of error codes to ignore.
            ignore_regex: Regex pattern for error codes to ignore.
            ignore_syntax: Whether to ignore syntax errors.
            message_template: Custom message template.
            verbosity: Verbosity level (1-3).
            strictness: Strictness level (short, long, full).
            **kwargs: Other tool options.
        """
        validate_list(ignore, "ignore")
        validate_str(ignore_regex, "ignore_regex")
        validate_bool(ignore_syntax, "ignore_syntax")
        validate_str(message_template, "message_template")
        validate_int(
            verbosity,
            "verbosity",
            min_value=DARGLINT_MIN_VERBOSITY,
            max_value=DARGLINT_MAX_VERBOSITY,
        )

        # Normalize strictness enum if provided
        if strictness is not None:
            strict_enum = normalize_darglint_strictness(strictness)
            strictness = strict_enum.name.lower()

        options = filter_none_options(
            ignore=ignore,
            ignore_regex=ignore_regex,
            ignore_syntax=ignore_syntax,
            message_template=message_template,
            verbosity=verbosity,
            strictness=strictness,
        )
        super().set_options(**options, **kwargs)

    def _build_command(self) -> list[str]:
        """Build the Darglint command.

        Returns:
            List of command arguments.
        """
        cmd: list[str] = self._get_executable_command("darglint")

        # Add configuration options
        ignore_opt = self.options.get("ignore")
        if ignore_opt is not None and isinstance(ignore_opt, list):
            cmd.extend(["--ignore", ",".join(str(i) for i in ignore_opt)])
        ignore_regex_opt = self.options.get("ignore_regex")
        if ignore_regex_opt is not None:
            cmd.extend(["--ignore-regex", str(ignore_regex_opt)])
        if self.options.get("ignore_syntax"):
            cmd.append("--ignore-syntax")
        verbosity_opt = self.options.get("verbosity")
        if verbosity_opt is not None:
            cmd.extend(["--verbosity", str(verbosity_opt)])
        strictness_opt = self.options.get("strictness")
        if strictness_opt is not None:
            cmd.extend(["--strictness", str(strictness_opt)])

        return cmd

    def _process_file(
        self,
        file_path: str,
        timeout: int,
    ) -> FileProcessResult:
        """Process a single file with Darglint.

        Args:
            file_path: Path to the file to process.
            timeout: Timeout in seconds for the subprocess execution.

        Returns:
            FileProcessResult: Result containing success status, issues, and output.
        """
        cmd: list[str] = self._build_command() + [str(file_path)]
        try:
            success: bool
            output: str
            success, output = self._run_subprocess(cmd=cmd, timeout=timeout)
            issues = parse_darglint_output(output=output)
            issues_count: int = len(issues)
            return FileProcessResult(
                success=success and issues_count == 0,
                issues_count=issues_count,
                issues=issues,
                output=output,
                timeout_issue=None,
            )
        except subprocess.TimeoutExpired:
            # Create a timeout issue object to display in the table
            timeout_issue = DarglintIssue(
                file=str(file_path),
                line=0,
                code="TIMEOUT",
                message=(
                    f"Darglint execution timed out "
                    f"({timeout}s limit exceeded). "
                    "This may indicate:\n"
                    "  - Large file taking too long to analyze\n"
                    "  - Complex docstrings requiring extensive parsing\n"
                    "  - Need to increase timeout via "
                    "--tool-options darglint:timeout=N"
                ),
            )
            return FileProcessResult(
                success=False,
                issues_count=0,
                issues=[],
                output=None,
                timeout_issue=timeout_issue,
            )
        except (OSError, ValueError, RuntimeError) as e:
            return FileProcessResult(
                success=False,
                issues_count=0,
                issues=[],
                output=f"Error processing {file_path}: {str(e)}",
                timeout_issue=None,
            )

    def _validate_timeout(
        self,
        timeout_value: object,
        default: int,
    ) -> int:
        """Validate and return a timeout value.

        Args:
            timeout_value: The timeout value to validate.
            default: Default value if invalid.

        Returns:
            Validated timeout as integer.
        """
        if isinstance(timeout_value, int) and timeout_value > 0:
            return timeout_value
        return default

    def check(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Check Python files for docstring issues with Darglint.

        Args:
            paths: List of file or directory paths to check.
            options: Runtime options that override defaults.

        Returns:
            ToolResult with check results.
        """
        # Get timeout from options (configured via pyproject.toml or set_options)
        configured_timeout_opt = self.options.get("timeout", DARGLINT_DEFAULT_TIMEOUT)
        configured_timeout = self._validate_timeout(
            configured_timeout_opt,
            DARGLINT_DEFAULT_TIMEOUT,
        )

        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(paths, options)
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        # Use the configured timeout instead of default
        timeout = configured_timeout

        all_outputs: list[str] = []
        all_issues: list[DarglintIssue] = []
        all_success: bool = True
        skipped_files: list[str] = []
        execution_failures: int = 0
        total_issues: int = 0

        # Show progress bar only when processing multiple files
        if len(ctx.files) >= 2:
            with click.progressbar(
                ctx.files,
                label="Processing files",
                bar_template="%(label)s  %(info)s",
            ) as bar:
                for file_path in bar:
                    result = self._process_file(
                        file_path=file_path,
                        timeout=timeout,
                    )
                    if not result.success:
                        all_success = False
                    total_issues += result.issues_count
                    if result.issues:
                        all_issues.extend(result.issues)
                    if result.output:
                        all_outputs.append(result.output)
                    if result.timeout_issue:
                        skipped_files.append(file_path)
                        execution_failures += 1
                        all_issues.append(result.timeout_issue)
                    elif (
                        not result.success
                        and not result.timeout_issue
                        and result.issues_count == 0
                        and result.output
                        and "Error" in result.output
                    ):
                        execution_failures += 1
                        error_issue = DarglintIssue(
                            file=str(file_path),
                            line=0,
                            code="EXEC_ERROR",
                            message=(
                                f"Execution error: {result.output.strip()}"
                                if result.output
                                else "Execution error during darglint processing"
                            ),
                        )
                        all_issues.append(error_issue)
        else:
            for file_path in ctx.files:
                result = self._process_file(file_path=file_path, timeout=timeout)
                if not result.success:
                    all_success = False
                total_issues += result.issues_count
                if result.issues:
                    all_issues.extend(result.issues)
                if result.output:
                    all_outputs.append(result.output)
                if result.timeout_issue:
                    skipped_files.append(file_path)
                    execution_failures += 1
                    all_issues.append(result.timeout_issue)
                elif (
                    not result.success
                    and not result.timeout_issue
                    and result.issues_count == 0
                    and result.output
                    and "Error" in result.output
                ):
                    execution_failures += 1
                    error_issue = DarglintIssue(
                        file=str(file_path),
                        line=0,
                        code="EXEC_ERROR",
                        message=(
                            f"Execution error: {result.output.strip()}"
                            if result.output
                            else "Execution error during darglint processing"
                        ),
                    )
                    all_issues.append(error_issue)

        output: str = "\n".join(all_outputs)
        if skipped_files:
            output += (
                f"\n\nSkipped {len(skipped_files)} file(s) due to timeout "
                f"({timeout}s limit exceeded):"
            )
            for file in skipped_files:
                output += f"\n  - {file}"

        final_output: str | None = output
        if not output:
            final_output = None

        # Include execution failures (timeouts/errors) in issues_count
        total_issues_with_failures = total_issues + execution_failures

        return ToolResult(
            name=self.definition.name,
            success=all_success,
            output=final_output,
            issues_count=total_issues_with_failures,
            issues=all_issues,
        )

    def fix(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Darglint cannot fix issues, only report them.

        Args:
            paths: List of file or directory paths to fix.
            options: Runtime options that override defaults.

        Raises:
            NotImplementedError: As Darglint does not support fixing issues.
        """
        raise NotImplementedError(
            "Darglint cannot automatically fix issues. Run 'lintro check' to see "
            "issues.",
        )
