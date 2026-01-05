"""Yamllint YAML linter integration - runner implementation.

This module provides an alternative implementation of YamllintTool
with per-file processing and progress tracking.
"""

import contextlib
import os
import subprocess  # nosec B404 - used safely with shell disabled
from typing import Any

import click
from loguru import logger

from lintro.models.core.tool_result import ToolResult
from lintro.parsers.yamllint.yamllint_parser import parse_yamllint_output
from lintro.tools.implementations.yamllint_config import (
    YAMLLINT_DEFAULT_TIMEOUT,
    YAMLLINT_FORMATS,
    YamllintTool,
)
from lintro.utils.path_filtering import walk_files_with_excludes


class YamllintRunner(YamllintTool):
    """Yamllint runner with per-file processing and progress tracking.

    This class extends YamllintTool with enhanced file processing
    capabilities including progress bars and detailed error handling.
    """

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
        file_cwd: str = self.get_cwd(paths=[abs_file])
        file_dir: str = os.path.dirname(abs_file)
        # Build command and discover config relative to file's directory
        cmd: list[str] = self._get_executable_command("yamllint")
        format_option: str = self.options.get("format", YAMLLINT_FORMATS[0])
        cmd.extend(["--format", format_option])
        # Discover config file relative to the file being checked
        config_file: str | None = self._find_yamllint_config(search_dir=file_dir)
        if config_file:
            # Ensure config file path is absolute so yamllint can find it
            # even when cwd is a subdirectory
            abs_config_file = os.path.abspath(config_file)
            cmd.extend(["--config-file", abs_config_file])
            logger.debug(
                f"[YamllintTool] Using config file: {abs_config_file} "
                f"(original: {config_file})",
            )
        config_data: str | None = self.options.get("config_data")
        if config_data:
            cmd.extend(["--config-data", config_data])
        if self.options.get("strict", False):
            cmd.append("--strict")
        if self.options.get("relaxed", False):
            cmd.append("--relaxed")
        if self.options.get("no_warnings", False):
            cmd.append("--no-warnings")
        cmd.append(abs_file)
        logger.debug(
            f"[YamllintTool] Processing file: {abs_file} (cwd={file_cwd})",
        )
        logger.debug(f"[YamllintTool] Command: {' '.join(cmd)}")
        try:
            success, output = self._run_subprocess(
                cmd=cmd,
                timeout=timeout,
                cwd=file_cwd,
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
        except FileNotFoundError:
            # File not found - treat as skipped/missing silently for user;
            # do not fail run
            return 0, [], False, False, True, True
        except OSError as e:
            # Check for "No such file or directory" error
            # (errno 2 on Unix, errno 3 on Windows)
            import errno

            if e.errno in (errno.ENOENT, errno.ENOTDIR):
                # treat as skipped/missing silently for user; do not fail run
                return 0, [], False, False, True, True
            # Other OSError - log and treat as execution failure
            err_msg = str(e)
            logger.debug(
                f"Yamllint execution error for {file_path}: {err_msg}",
            )
            return 0, [], False, True, False, False
        except Exception as e:
            # Log execution errors for debugging while keeping user output clean
            err_msg = str(e)
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
        # Check version requirements
        version_result = self._verify_tool_version()
        if version_result is not None:
            return version_result

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
        logger.debug(
            f"[YamllintTool] Discovered {len(yaml_files)} files matching patterns: "
            f"{self.config.file_patterns}",
        )
        logger.debug(
            f"[YamllintTool] Exclude patterns applied: {self.exclude_patterns}",
        )
        if yaml_files:
            logger.debug(
                f"[YamllintTool] Files to check (first 10): {yaml_files[:10]}",
            )
        # Check for yamllint config files
        config_paths = [
            ".yamllint",
            ".yamllint.yml",
            ".yamllint.yaml",
            "setup.cfg",
            "pyproject.toml",
        ]
        found_config = None
        config_file_option = self.options.get("config_file")
        if config_file_option:
            found_config = os.path.abspath(config_file_option)
            logger.debug(
                f"[YamllintTool] Using explicit config file: {found_config}",
            )
        else:
            for config_name in config_paths:
                config_path = os.path.abspath(config_name)
                if os.path.exists(config_path):
                    found_config = config_path
                    logger.debug(
                        f"[YamllintTool] Found config file: {config_path}",
                    )
                    break
        if not found_config:
            logger.debug(
                "[YamllintTool] No yamllint config file found (using defaults)",
            )
        # Load ignore patterns from yamllint config and filter files
        ignore_patterns: list[str] = self._load_yamllint_ignore_patterns(
            config_file=found_config,
        )
        if ignore_patterns:
            original_count = len(yaml_files)
            yaml_files = [
                f
                for f in yaml_files
                if not self._should_ignore_file(
                    file_path=f,
                    ignore_patterns=ignore_patterns,
                )
            ]
            filtered_count = original_count - len(yaml_files)
            if filtered_count > 0:
                logger.debug(
                    f"[YamllintTool] Filtered out {filtered_count} files based on "
                    f"yamllint ignore patterns: {ignore_patterns}",
                )
        logger.debug(f"Files to check: {yaml_files}")
        timeout: int = self.options.get("timeout", YAMLLINT_DEFAULT_TIMEOUT)
        # Aggregate parsed issues across files and rely on table renderers upstream
        all_success: bool = True
        all_issues: list[Any] = []
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
                    f"Failed to process {other_execution_failures} file(s) due to "
                    "execution errors",
                )
            output = "\n".join(output_lines) if output_lines else None
        return ToolResult(
            name=self.name,
            success=all_success,
            output=output,
            issues_count=total_issues,
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
