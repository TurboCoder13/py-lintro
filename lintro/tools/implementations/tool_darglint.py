"""Darglint docstring linter integration."""

import subprocess  # nosec B404 - vetted use via BaseTool._run_subprocess
from dataclasses import dataclass, field

import click
from loguru import logger

from lintro.enums.darglint_strictness import (
    DarglintStrictness,
    normalize_darglint_strictness,
)
from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_config import ToolConfig
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.darglint.darglint_issue import DarglintIssue
from lintro.parsers.darglint.darglint_parser import parse_darglint_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.config_utils import load_darglint_config

# Constants for Darglint configuration
# Reduced to 15s to fail fast on problematic files while allowing
# normal files to complete. Increase via --tool-options darglint:timeout=N
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


@dataclass
class DarglintTool(BaseTool):
    """Darglint docstring linter integration.

    Darglint is a Python docstring linter that checks docstring style and completeness.
    It verifies that docstrings match the function signature and contain all required
    sections.

    Attributes:
        name: str: Tool name.
        description: str: Tool description.
        can_fix: bool: Whether the core can fix issues.
        config: ToolConfig: Tool configuration.
        exclude_patterns: list[str]: List of patterns to exclude.
        include_venv: bool: Whether to include virtual environment files.
    """

    name: str = "darglint"
    description: str = (
        "Python docstring linter that checks docstring style and completeness"
    )
    can_fix: bool = field(default=False)  # Darglint can only check, not fix
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=DARGLINT_DEFAULT_PRIORITY,  # Lower priority than formatters, \
            # slightly lower than flake8
            conflicts_with=[],  # No direct conflicts
            file_patterns=DARGLINT_FILE_PATTERNS,  # Only applies to Python files
            tool_type=ToolType.LINTER,
            options={
                "timeout": DARGLINT_DEFAULT_TIMEOUT,  # Default timeout in seconds \
                # per file
                "ignore": None,  # List of error codes to ignore
                "ignore_regex": None,  # Regex pattern for error codes to ignore
                "ignore_syntax": False,  # Whether to ignore syntax errors
                "message_template": None,  # Custom message template
                "verbosity": DARGLINT_DEFAULT_VERBOSITY,  # Verbosity level (1-3) - \
                # use 2 for descriptive messages
                "strictness": DARGLINT_DEFAULT_STRICTNESS,  # Strictness level \
                # (short, long, full)
            },
        ),
    )

    def __post_init__(self) -> None:
        """Initialize the tool with configuration from pyproject.toml."""
        super().__post_init__()

        # Load darglint configuration from pyproject.toml
        darglint_config = load_darglint_config()

        # Apply exclude_dirs as exclude patterns
        # Use /* instead of /** since path_filtering.should_exclude_path
        # handles /* patterns but not ** recursive globs
        if "exclude_dirs" in darglint_config:
            exclude_dirs = darglint_config["exclude_dirs"]
            if isinstance(exclude_dirs, list):
                for exclude_dir in exclude_dirs:
                    pattern = f"{exclude_dir}/*"
                    if pattern not in self.exclude_patterns:
                        self.exclude_patterns.append(pattern)

    def set_options(
        self,
        ignore: list[str] | None = None,
        ignore_regex: str | None = None,
        ignore_syntax: bool | None = None,
        message_template: str | None = None,
        verbosity: int | None = None,
        strictness: str | DarglintStrictness | None = None,
        **kwargs,
    ) -> None:
        """Set Darglint-specific options.

        Args:
            ignore: list[str] | None: List of error codes to ignore.
            ignore_regex: str | None: Regex pattern for error codes to ignore.
            ignore_syntax: bool | None: Whether to ignore syntax errors.
            message_template: str | None: Custom message template.
            verbosity: int | None: Verbosity level (1-3).
            strictness: str | None: Strictness level (short, long, full).
            **kwargs: Other core options.

        Raises:
            ValueError: If an option value is invalid.
        """
        if ignore is not None and not isinstance(ignore, list):
            raise ValueError("ignore must be a list of error codes")
        if ignore_regex is not None and not isinstance(ignore_regex, str):
            raise ValueError("ignore_regex must be a string")
        if ignore_syntax is not None and not isinstance(ignore_syntax, bool):
            raise ValueError("ignore_syntax must be a boolean")
        if message_template is not None and not isinstance(message_template, str):
            raise ValueError("message_template must be a string")
        if verbosity is not None:
            if not isinstance(verbosity, int):
                raise ValueError("verbosity must be an integer")
            if not DARGLINT_MIN_VERBOSITY <= verbosity <= DARGLINT_MAX_VERBOSITY:
                raise ValueError(
                    f"verbosity must be between {DARGLINT_MIN_VERBOSITY} and "
                    f"{DARGLINT_MAX_VERBOSITY}",
                )
        if strictness is not None:
            strict_enum = normalize_darglint_strictness(
                strictness,
            )
            strictness = strict_enum.name.lower()

        options: dict[str, object] = {
            "ignore": ignore,
            "ignore_regex": ignore_regex,
            "ignore_syntax": ignore_syntax,
            "message_template": message_template,
            "verbosity": verbosity,
            "strictness": strictness,
        }
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _build_command(self) -> list[str]:
        """Build the Darglint command.

        Returns:
            list[str]: List of command arguments.
        """
        # Prefer running via the active environment (uv run) if available,
        # falling back to a direct executable when necessary.
        cmd: list[str] = self._get_executable_command("darglint")

        # Add configuration options
        if self.options.get("ignore"):
            cmd.extend(["--ignore", ",".join(self.options["ignore"])])
        if self.options.get("ignore_regex"):
            cmd.extend(["--ignore-regex", self.options["ignore_regex"]])
        if self.options.get("ignore_syntax"):
            cmd.append("--ignore-syntax")
        # Remove message_template override to use default output
        # if self.options.get("message_template"):
        #     cmd.extend(["--message-template", self.options["message_template"]])
        if self.options.get("verbosity"):
            cmd.extend(["--verbosity", str(self.options["verbosity"])])
        if self.options.get("strictness"):
            cmd.extend(["--strictness", self.options["strictness"]])

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
        except Exception as e:
            return FileProcessResult(
                success=False,
                issues_count=0,
                issues=[],
                output=f"Error processing {file_path}: {str(e)}",
                timeout_issue=None,
            )

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check Python files for docstring issues with Darglint.

        Args:
            paths: list[str]: List of file or directory paths to check.

        Returns:
            ToolResult: ToolResult instance.
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(
            paths,
            default_timeout=DARGLINT_DEFAULT_TIMEOUT,
        )
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        logger.debug(f"Files to check: {ctx.files}")
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
                        timeout=ctx.timeout,
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
                        # Only count as execution failure if no lint issues were found
                        # and there's an actual error (not just lint findings)
                        execution_failures += 1
                        # Create an execution error issue to keep issues consistent
                        # with issues_count
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
            # Process without progress bar for single file or no files
            for file_path in ctx.files:
                result = self._process_file(file_path=file_path, timeout=ctx.timeout)
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
                    # Only count as execution failure if no lint issues were found
                    # and there's an actual error (not just lint findings)
                    execution_failures += 1
                    # Create an execution error issue to keep issues consistent
                    # with issues_count
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
                f"({ctx.timeout}s limit exceeded):"
            )
            for file in skipped_files:
                output += f"\n  - {file}"

        if not output:
            output = None

        # Include execution failures (timeouts/errors) in issues_count
        # to properly reflect tool failure status
        total_issues_with_failures = total_issues + execution_failures

        return ToolResult(
            name=self.name,
            success=all_success,
            output=output,
            issues_count=total_issues_with_failures,
            issues=all_issues,
        )

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Darglint cannot fix issues, only report them.

        Args:
            paths: list[str]: List of file or directory paths to fix.

        Raises:
            NotImplementedError: As Darglint does not support fixing issues.
        """
        raise NotImplementedError(
            "Darglint cannot automatically fix issues. Run 'lintro check' to see "
            "issues.",
        )
