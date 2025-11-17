"""Yamllint YAML linter integration."""

import contextlib
import os
import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass, field

import click
from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.enums.yamllint_format import (
    YamllintFormat,
    normalize_yamllint_format,
)
from lintro.models.core.tool import ToolConfig, ToolResult
from lintro.parsers.yamllint.yamllint_parser import parse_yamllint_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes

# Constants
YAMLLINT_DEFAULT_TIMEOUT: int = 15
YAMLLINT_DEFAULT_PRIORITY: int = 40
YAMLLINT_FILE_PATTERNS: list[str] = [
    "*.yml",
    "*.yaml",
    ".yamllint",
    ".yamllint.yml",
    ".yamllint.yaml",
]
YAMLLINT_FORMATS: tuple[str, ...] = tuple(m.name.lower() for m in YamllintFormat)


@dataclass
class YamllintTool(BaseTool):
    """Yamllint YAML linter integration.

    Yamllint is a linter for YAML files that checks for syntax errors,
    formatting issues, and other YAML best practices.

    Attributes:
        name: Tool name
        description: Tool description
        can_fix: Whether the tool can fix issues
        config: Tool configuration
        exclude_patterns: List of patterns to exclude
        include_venv: Whether to include virtual environment files
    """

    name: str = "yamllint"
    description: str = "YAML linter for syntax and style checking"
    can_fix: bool = False
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=YAMLLINT_DEFAULT_PRIORITY,
            conflicts_with=[],
            file_patterns=YAMLLINT_FILE_PATTERNS,
            tool_type=ToolType.LINTER,
            options={
                "timeout": YAMLLINT_DEFAULT_TIMEOUT,
                # Use parsable by default; aligns with parser expectations
                "format": "parsable",
                "config_file": None,
                "config_data": None,
                "strict": False,
                "relaxed": False,
                "no_warnings": False,
            },
        ),
    )

    def __post_init__(self) -> None:
        """Initialize the tool."""
        super().__post_init__()

    def set_options(
        self,
        format: str | YamllintFormat | None = None,
        config_file: str | None = None,
        config_data: str | None = None,
        strict: bool | None = None,
        relaxed: bool | None = None,
        no_warnings: bool | None = None,
        **kwargs,
    ) -> None:
        """Set Yamllint-specific options.

        Args:
            format: Output format (parsable, standard, colored, github, auto)
            config_file: Path to yamllint config file
            config_data: Inline config data (YAML string)
            strict: Return non-zero exit code on warnings as well as errors
            relaxed: Use relaxed configuration
            no_warnings: Output only error level problems
            **kwargs: Other tool options

        Raises:
            ValueError: If an option value is invalid
        """
        if format is not None:
            # Accept both enum and string values for backward compatibility
            fmt_enum = normalize_yamllint_format(format)  # type: ignore[arg-type]
            format = fmt_enum.name.lower()
        if config_file is not None and not isinstance(config_file, str):
            raise ValueError("config_file must be a string path")
        if config_data is not None and not isinstance(config_data, str):
            raise ValueError("config_data must be a YAML string")
        if strict is not None and not isinstance(strict, bool):
            raise ValueError("strict must be a boolean")
        if relaxed is not None and not isinstance(relaxed, bool):
            raise ValueError("relaxed must be a boolean")
        if no_warnings is not None and not isinstance(no_warnings, bool):
            raise ValueError("no_warnings must be a boolean")
        options = {
            "format": format,
            "config_file": config_file,
            "config_data": config_data,
            "strict": strict,
            "relaxed": relaxed,
            "no_warnings": no_warnings,
        }
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _build_command(self) -> list[str]:
        """Build the yamllint command.

        Returns:
            list[str]: Command arguments for yamllint.
        """
        cmd: list[str] = self._get_executable_command("yamllint")
        format_option: str = self.options.get("format", YAMLLINT_FORMATS[0])
        cmd.extend(["--format", format_option])
        config_file: str | None = self.options.get("config_file")
        if config_file:
            cmd.extend(["--config-file", config_file])
        config_data: str | None = self.options.get("config_data")
        if config_data:
            cmd.extend(["--config-data", config_data])
        if self.options.get("strict", False):
            cmd.append("--strict")
        if self.options.get("relaxed", False):
            cmd.append("--relaxed")
        if self.options.get("no_warnings", False):
            cmd.append("--no-warnings")
        return cmd

    def _process_yaml_file(
        self,
        file_path: str,
        timeout: int,
    ) -> tuple[int, list, bool, bool, bool, bool]:
        """Process a single YAML file with yamllint.

        Args:
            file_path: Path to the YAML file to process.
            timeout: Timeout in seconds for the subprocess call.

        Returns:
            tuple containing:
                - issues_count: Number of issues found
                - issues_list: List of parsed issues
                - skipped_flag: True if file was skipped due to timeout
                - execution_failure_flag: True if there was an execution failure
                - success_flag: False if issues were found
                - should_continue: True if file should be silently skipped
                    (missing file)
        """
        # Use absolute path; run with the file's parent as cwd so that
        # yamllint discovers any local .yamllint config beside the file.
        abs_file: str = os.path.abspath(file_path)
        cmd: list[str] = self._build_command() + [abs_file]
        try:
            success, output = self._run_subprocess(
                cmd=cmd,
                timeout=timeout,
                cwd=self.get_cwd(paths=[abs_file]),
            )
            issues = parse_yamllint_output(output=output)
            issues_count: int = len(issues)
            # Yamllint returns 1 on errors/warnings unless --no-warnings/relaxed
            # Use parsed issues to determine success and counts reliably.
            # Honor subprocess exit status: if it failed and we have no parsed
            # issues, that's an execution failure (invalid config, crash,
            # missing dependency, etc.)
            # The 'success' flag from _run_subprocess reflects the subprocess
            # exit status
            success_flag: bool = success and issues_count == 0
            # Execution failure occurs when subprocess failed but no lint issues
            # were found
            # This distinguishes execution errors from lint findings
            execution_failure = not success and issues_count == 0
            # Log execution failures with error details for debugging
            if execution_failure and output:
                logger.debug(
                    f"Yamllint execution failure for {file_path}: {output}",
                )
            return issues_count, issues, False, execution_failure, success_flag, False
        except subprocess.TimeoutExpired:
            # Count timeout as an execution failure
            return 0, [], True, True, False, False
        except Exception as e:
            # Suppress missing file noise in console output; keep as debug
            err_msg = str(e)
            if "No such file or directory" in err_msg:
                # treat as skipped/missing silently for user; do not fail run
                return 0, [], False, False, True, True
            # Log execution errors for debugging while keeping user output clean
            logger.debug(
                f"Yamllint execution error for {file_path}: {err_msg}",
            )
            # Do not add raw errors to user-facing output; mark failure only
            # Count execution errors as failures
            return 0, [], False, True, False, False

    def _process_yaml_file_result(
        self,
        issues_count: int,
        issues: list,
        skipped_flag: bool,
        execution_failure_flag: bool,
        success_flag: bool,
        file_path: str,
        all_success: bool,
        all_issues: list,
        skipped_files: list[str],
        timeout_skipped_count: int,
        other_execution_failures: int,
        total_issues: int,
    ) -> tuple[bool, list, list[str], int, int, int]:
        """Process a single file's result and update accumulators.

        Args:
            issues_count: Number of issues found in the file.
            issues: List of parsed issues.
            skipped_flag: True if file was skipped due to timeout.
            execution_failure_flag: True if there was an execution failure.
            success_flag: False if issues were found.
            file_path: Path to the file being processed.
            all_success: Current overall success flag.
            all_issues: Current list of all issues.
            skipped_files: Current list of skipped files.
            timeout_skipped_count: Current count of timeout skips.
            other_execution_failures: Current count of execution failures.
            total_issues: Current total issue count.

        Returns:
            tuple containing updated accumulators:
                (all_success, all_issues, skipped_files,
                 timeout_skipped_count, other_execution_failures, total_issues)
        """
        if not success_flag:
            all_success = False
        total_issues += issues_count
        if issues:
            all_issues.extend(issues)
        if skipped_flag:
            skipped_files.append(file_path)
            all_success = False
            timeout_skipped_count += 1
        elif execution_failure_flag:
            # Only count execution failures if not already counted as skipped
            all_success = False
            other_execution_failures += 1
        return (
            all_success,
            all_issues,
            skipped_files,
            timeout_skipped_count,
            other_execution_failures,
            total_issues,
        )

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files with Yamllint.

        Args:
            paths: list[str]: List of file or directory paths to check.

        Returns:
            ToolResult: Result of the check operation.
        """
        self._validate_paths(paths=paths)
        if not paths:
            return ToolResult(
                name=self.name,
                success=True,
                output="No files to check.",
                issues_count=0,
            )
        yaml_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )
        logger.debug(f"Files to check: {yaml_files}")
        timeout: int = self.options.get("timeout", YAMLLINT_DEFAULT_TIMEOUT)
        # Aggregate parsed issues across files and rely on table renderers upstream
        all_success: bool = True
        all_issues: list = []
        skipped_files: list[str] = []
        timeout_skipped_count: int = 0
        other_execution_failures: int = 0
        total_issues: int = 0

        # Show progress bar only when processing multiple files
        if len(yaml_files) >= 2:
            files_to_iterate = click.progressbar(
                yaml_files,
                label="Processing files",
                bar_template="%(label)s  %(info)s",
            )
            context_mgr = files_to_iterate
        else:
            files_to_iterate = yaml_files
            context_mgr = contextlib.nullcontext()

        with context_mgr:
            for file_path in files_to_iterate:
                (
                    issues_count,
                    issues,
                    skipped_flag,
                    execution_failure_flag,
                    success_flag,
                    should_continue,
                ) = self._process_yaml_file(file_path=file_path, timeout=timeout)
                if should_continue:
                    continue
                (
                    all_success,
                    all_issues,
                    skipped_files,
                    timeout_skipped_count,
                    other_execution_failures,
                    total_issues,
                ) = self._process_yaml_file_result(
                    issues_count=issues_count,
                    issues=issues,
                    skipped_flag=skipped_flag,
                    execution_failure_flag=execution_failure_flag,
                    success_flag=success_flag,
                    file_path=file_path,
                    all_success=all_success,
                    all_issues=all_issues,
                    skipped_files=skipped_files,
                    timeout_skipped_count=timeout_skipped_count,
                    other_execution_failures=other_execution_failures,
                    total_issues=total_issues,
                )
        # Build output message if there are skipped files or execution failures
        output: str | None = None
        if timeout_skipped_count > 0 or other_execution_failures > 0:
            output_lines: list[str] = []
            if timeout_skipped_count > 0:
                output_lines.append(
                    f"Skipped {timeout_skipped_count} file(s) due to timeout "
                    f"({timeout}s limit exceeded):",
                )
                for file in skipped_files:
                    output_lines.append(f"  - {file}")
            if other_execution_failures > 0:
                output_lines.append(
                    f"Failed to process {other_execution_failures} file(s) "
                    "due to execution errors",
                )
            output = "\n".join(output_lines) if output_lines else None
        # Include execution failures (timeouts/errors) in issues_count
        # to properly reflect tool failure status
        total_issues_with_failures = total_issues + other_execution_failures
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
        """Yamllint cannot fix issues, only report them.

        Args:
            paths: list[str]: List of file or directory paths to fix.

        Returns:
            ToolResult: Result indicating that fixing is not supported.
        """
        return ToolResult(
            name=self.name,
            success=False,
            output=(
                "Yamllint is a linter only and cannot fix issues. Use a YAML "
                "formatter like Prettier for formatting."
            ),
            issues_count=0,
        )
