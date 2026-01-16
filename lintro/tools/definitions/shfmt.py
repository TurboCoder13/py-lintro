"""Shfmt tool definition.

Shfmt is a shell script formatter that supports POSIX, Bash, and mksh shells.
It formats shell scripts to ensure consistent style and can detect formatting
issues in diff mode.
"""

from __future__ import annotations

import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass
from typing import Any

import click
from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.shfmt.shfmt_parser import parse_shfmt_output
from lintro.plugins.base import BaseToolPlugin
from lintro.plugins.protocol import ToolDefinition
from lintro.plugins.registry import register_tool
from lintro.tools.core.option_validators import (
    filter_none_options,
    validate_bool,
    validate_int,
    validate_str,
)

# Constants for shfmt configuration
SHFMT_DEFAULT_TIMEOUT: int = 30
SHFMT_DEFAULT_PRIORITY: int = 50
SHFMT_FILE_PATTERNS: list[str] = ["*.sh", "*.bash", "*.ksh"]


@register_tool
@dataclass
class ShfmtPlugin(BaseToolPlugin):
    """Shfmt shell script formatter plugin.

    This plugin integrates shfmt with Lintro for formatting shell scripts.
    It supports POSIX, Bash, and mksh shells with various formatting options.
    """

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition.

        Returns:
            ToolDefinition containing tool metadata.
        """
        return ToolDefinition(
            name="shfmt",
            description=(
                "Shell script formatter supporting POSIX, Bash, and mksh shells"
            ),
            can_fix=True,
            tool_type=ToolType.FORMATTER,
            file_patterns=SHFMT_FILE_PATTERNS,
            priority=SHFMT_DEFAULT_PRIORITY,
            conflicts_with=[],
            native_configs=[".editorconfig"],
            version_command=["shfmt", "--version"],
            min_version="3.7.0",
            default_options={
                "timeout": SHFMT_DEFAULT_TIMEOUT,
                "indent": None,
                "binary_next_line": False,
                "switch_case_indent": False,
                "space_redirects": False,
                "language_dialect": None,
                "simplify": False,
            },
            default_timeout=SHFMT_DEFAULT_TIMEOUT,
        )

    def set_options(  # type: ignore[override]
        self,
        indent: int | None = None,
        binary_next_line: bool | None = None,
        switch_case_indent: bool | None = None,
        space_redirects: bool | None = None,
        language_dialect: str | None = None,
        simplify: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Set shfmt-specific options.

        Args:
            indent: Indentation size. 0 for tabs, >0 for that many spaces.
            binary_next_line: Binary ops like && and | may start a line.
            switch_case_indent: Indent switch cases.
            space_redirects: Redirect operators followed by space.
            language_dialect: Shell language dialect (bash, posix, mksh, bats).
            simplify: Simplify code where possible.
            **kwargs: Other tool options.

        Raises:
            ValueError: If language_dialect is not a valid dialect.
        """
        validate_int(indent, "indent")
        validate_bool(binary_next_line, "binary_next_line")
        validate_bool(switch_case_indent, "switch_case_indent")
        validate_bool(space_redirects, "space_redirects")
        validate_str(language_dialect, "language_dialect")
        validate_bool(simplify, "simplify")

        # Validate language_dialect if provided
        if language_dialect is not None:
            valid_dialects = {"bash", "posix", "mksh", "bats"}
            if language_dialect.lower() not in valid_dialects:
                msg = (
                    f"Invalid language_dialect: {language_dialect!r}. "
                    f"Must be one of: {', '.join(sorted(valid_dialects))}"
                )
                raise ValueError(msg)
            language_dialect = language_dialect.lower()

        options = filter_none_options(
            indent=indent,
            binary_next_line=binary_next_line,
            switch_case_indent=switch_case_indent,
            space_redirects=space_redirects,
            language_dialect=language_dialect,
            simplify=simplify,
        )
        super().set_options(**options, **kwargs)

    def _build_common_args(self) -> list[str]:
        """Build common CLI arguments for shfmt.

        Returns:
            CLI arguments for shfmt.
        """
        args: list[str] = []

        # Indentation
        indent = self.options.get("indent")
        if indent is not None:
            args.extend(["-i", str(indent)])

        # Binary operations at start of line
        if self.options.get("binary_next_line"):
            args.append("-bn")

        # Switch case indentation
        if self.options.get("switch_case_indent"):
            args.append("-ci")

        # Space after redirect operators
        if self.options.get("space_redirects"):
            args.append("-sr")

        # Language dialect
        language_dialect = self.options.get("language_dialect")
        if language_dialect is not None:
            args.extend(["-ln", str(language_dialect)])

        # Simplify code
        if self.options.get("simplify"):
            args.append("-s")

        return args

    def _process_single_file_check(
        self,
        file_path: str,
        timeout: int,
        cwd: str | None,
        results: dict[str, Any],
    ) -> None:
        """Process a single file in check mode.

        Args:
            file_path: Path to the shell script to check.
            timeout: Timeout in seconds for the shfmt command.
            cwd: Working directory for the command.
            results: Dictionary to accumulate results across files.
        """
        cmd = self._get_executable_command(tool_name="shfmt") + ["-d"]
        cmd.extend(self._build_common_args())
        cmd.append(file_path)

        try:
            success, output = self._run_subprocess(
                cmd=cmd,
                timeout=timeout,
                cwd=cwd,
            )
            issues = parse_shfmt_output(output=output)
            issues_count = len(issues)

            if not success:
                results["all_success"] = False
            results["total_issues"] += issues_count

            if not success or issues:
                results["all_outputs"].append(output)
            if issues:
                results["all_issues"].extend(issues)
        except subprocess.TimeoutExpired:
            results["skipped_files"].append(file_path)
            results["all_success"] = False
            results["execution_failures"] += 1
        except (OSError, ValueError, RuntimeError) as e:
            results["all_outputs"].append(f"Error processing {file_path}: {e!s}")
            results["all_success"] = False
            results["execution_failures"] += 1

    def _process_single_file_fix(
        self,
        file_path: str,
        timeout: int,
        cwd: str | None,
        results: dict[str, Any],
    ) -> None:
        """Process a single file in fix mode.

        Args:
            file_path: Path to the shell script to fix.
            timeout: Timeout in seconds for the shfmt command.
            cwd: Working directory for the command.
            results: Dictionary to accumulate results across files.
        """
        # First check if file needs formatting
        check_cmd = self._get_executable_command(tool_name="shfmt") + ["-d"]
        check_cmd.extend(self._build_common_args())
        check_cmd.append(file_path)

        try:
            check_success, check_output = self._run_subprocess(
                cmd=check_cmd,
                timeout=timeout,
                cwd=cwd,
            )
            check_issues = parse_shfmt_output(output=check_output)

            if check_issues:
                results["initial_issues"] += len(check_issues)

                # Apply fix with -w flag
                fix_cmd = self._get_executable_command(tool_name="shfmt") + ["-w"]
                fix_cmd.extend(self._build_common_args())
                fix_cmd.append(file_path)

                fix_success, _ = self._run_subprocess(
                    cmd=fix_cmd,
                    timeout=timeout,
                    cwd=cwd,
                )

                if fix_success:
                    results["fixed_issues"] += len(check_issues)
                    results["fixed_files"].append(file_path)
                else:
                    results["all_success"] = False
                    results["remaining_issues"] += len(check_issues)
                    results["all_issues"].extend(check_issues)

        except subprocess.TimeoutExpired:
            results["skipped_files"].append(file_path)
            results["all_success"] = False
            results["execution_failures"] += 1
        except (OSError, ValueError, RuntimeError) as e:
            results["all_outputs"].append(f"Error processing {file_path}: {e!s}")
            results["all_success"] = False
            results["execution_failures"] += 1

    def check(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Check files with shfmt.

        Args:
            paths: List of file or directory paths to check.
            options: Runtime options that override defaults.

        Returns:
            ToolResult with check results.
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(paths, options)
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        shell_files = ctx.files

        # Accumulate results across all files
        results: dict[str, Any] = {
            "all_outputs": [],
            "all_issues": [],
            "all_success": True,
            "skipped_files": [],
            "execution_failures": 0,
            "total_issues": 0,
        }

        # Show progress bar only when processing multiple files
        if len(shell_files) >= 2:
            with click.progressbar(
                shell_files,
                label="Processing files",
                bar_template="%(label)s  %(info)s",
            ) as bar:
                for file_path in bar:
                    self._process_single_file_check(
                        file_path=file_path,
                        timeout=ctx.timeout,
                        cwd=ctx.cwd,
                        results=results,
                    )
        else:
            for file_path in shell_files:
                self._process_single_file_check(
                    file_path=file_path,
                    timeout=ctx.timeout,
                    cwd=ctx.cwd,
                    results=results,
                )

        # Build output from accumulated results
        output: str = (
            "\n".join(results["all_outputs"]) if results["all_outputs"] else ""
        )
        if results["execution_failures"] > 0:
            if output:
                output += "\n\n"
            if results["skipped_files"]:
                output += (
                    f"Skipped/failed {results['execution_failures']} file(s) due to "
                    f"execution failures (including timeouts)"
                )
                output += f" (timeout: {ctx.timeout}s):"
                for file in results["skipped_files"]:
                    output += f"\n  - {file}"
            else:
                output += (
                    f"Failed to process {results['execution_failures']} file(s) "
                    "due to execution errors"
                )

        final_output: str | None = output if output.strip() else None

        return ToolResult(
            name=self.definition.name,
            success=results["all_success"] and results["total_issues"] == 0,
            output=final_output,
            issues_count=results["total_issues"],
            issues=results["all_issues"],
        )

    def fix(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Fix formatting issues in files with shfmt.

        Args:
            paths: List of file or directory paths to fix.
            options: Runtime options that override defaults.

        Returns:
            ToolResult with fix results.
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(
            paths,
            options,
            no_files_message="No files to format.",
        )
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        shell_files = ctx.files

        # Accumulate results across all files
        results: dict[str, Any] = {
            "all_outputs": [],
            "all_issues": [],
            "all_success": True,
            "skipped_files": [],
            "execution_failures": 0,
            "initial_issues": 0,
            "fixed_issues": 0,
            "remaining_issues": 0,
            "fixed_files": [],
        }

        # Show progress bar only when processing multiple files
        if len(shell_files) >= 2:
            with click.progressbar(
                shell_files,
                label="Formatting files",
                bar_template="%(label)s  %(info)s",
            ) as bar:
                for file_path in bar:
                    self._process_single_file_fix(
                        file_path=file_path,
                        timeout=ctx.timeout,
                        cwd=ctx.cwd,
                        results=results,
                    )
        else:
            for file_path in shell_files:
                self._process_single_file_fix(
                    file_path=file_path,
                    timeout=ctx.timeout,
                    cwd=ctx.cwd,
                    results=results,
                )

        # Build summary output
        summary_parts: list[str] = []
        if results["fixed_issues"] > 0:
            summary_parts.append(
                f"Fixed {results['fixed_issues']} issue(s) in "
                f"{len(results['fixed_files'])} file(s)",
            )
        if results["remaining_issues"] > 0:
            summary_parts.append(
                f"Found {results['remaining_issues']} issue(s) that could not be fixed",
            )
        if results["execution_failures"] > 0:
            summary_parts.append(
                f"Failed to process {results['execution_failures']} file(s)",
            )

        final_output = "\n".join(summary_parts) if summary_parts else "No fixes needed."

        logger.debug(
            f"[ShfmtPlugin] Fix complete: initial={results['initial_issues']}, "
            f"fixed={results['fixed_issues']}, remaining={results['remaining_issues']}",
        )

        return ToolResult(
            name=self.definition.name,
            success=results["all_success"] and results["remaining_issues"] == 0,
            output=final_output,
            issues_count=results["remaining_issues"],
            issues=results["all_issues"],
            initial_issues_count=results["initial_issues"],
            fixed_issues_count=results["fixed_issues"],
            remaining_issues_count=results["remaining_issues"],
        )
