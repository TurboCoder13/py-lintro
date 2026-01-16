"""Shellcheck tool definition.

ShellCheck is a static analysis tool for shell scripts. It identifies bugs,
syntax issues, and suggests improvements for bash/sh/dash/ksh/zsh scripts.
"""

from __future__ import annotations

import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass
from typing import Any

import click

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.shellcheck.shellcheck_parser import parse_shellcheck_output
from lintro.plugins.base import BaseToolPlugin
from lintro.plugins.protocol import ToolDefinition
from lintro.plugins.registry import register_tool
from lintro.tools.core.option_validators import (
    filter_none_options,
    validate_list,
    validate_str,
)

# Constants for Shellcheck configuration
SHELLCHECK_DEFAULT_TIMEOUT: int = 30
SHELLCHECK_DEFAULT_PRIORITY: int = 50
SHELLCHECK_FILE_PATTERNS: list[str] = ["*.sh", "*.bash", "*.ksh", "*.zsh"]
SHELLCHECK_DEFAULT_FORMAT: str = "json1"
SHELLCHECK_DEFAULT_SEVERITY: str = "style"

# Valid severity levels for shellcheck
SHELLCHECK_SEVERITY_LEVELS: tuple[str, ...] = ("error", "warning", "info", "style")

# Valid shell dialects for shellcheck
SHELLCHECK_SHELL_DIALECTS: tuple[str, ...] = ("bash", "sh", "dash", "ksh", "zsh")


def normalize_shellcheck_severity(value: str) -> str:
    """Normalize shellcheck severity level.

    Args:
        value: Severity level string to normalize.

    Returns:
        Normalized severity level string (lowercase).

    Raises:
        ValueError: If the severity level is not valid.
    """
    normalized = value.lower()
    if normalized not in SHELLCHECK_SEVERITY_LEVELS:
        valid = ", ".join(SHELLCHECK_SEVERITY_LEVELS)
        raise ValueError(f"Invalid severity level: {value!r}. Valid levels: {valid}")
    return normalized


def normalize_shellcheck_shell(value: str) -> str:
    """Normalize shellcheck shell dialect.

    Args:
        value: Shell dialect string to normalize.

    Returns:
        Normalized shell dialect string (lowercase).

    Raises:
        ValueError: If the shell dialect is not valid.
    """
    normalized = value.lower()
    if normalized not in SHELLCHECK_SHELL_DIALECTS:
        valid = ", ".join(SHELLCHECK_SHELL_DIALECTS)
        raise ValueError(f"Invalid shell dialect: {value!r}. Valid dialects: {valid}")
    return normalized


@register_tool
@dataclass
class ShellcheckPlugin(BaseToolPlugin):
    """ShellCheck shell script linter plugin.

    This plugin integrates ShellCheck with Lintro for checking shell scripts
    against best practices and identifying potential bugs.
    """

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition.

        Returns:
            ToolDefinition containing tool metadata.
        """
        return ToolDefinition(
            name="shellcheck",
            description=(
                "Static analysis tool for shell scripts that identifies bugs and "
                "suggests improvements"
            ),
            can_fix=False,
            tool_type=ToolType.LINTER,
            file_patterns=SHELLCHECK_FILE_PATTERNS,
            priority=SHELLCHECK_DEFAULT_PRIORITY,
            conflicts_with=[],
            native_configs=[".shellcheckrc"],
            version_command=["shellcheck", "--version"],
            min_version="0.9.0",
            default_options={
                "timeout": SHELLCHECK_DEFAULT_TIMEOUT,
                "format": SHELLCHECK_DEFAULT_FORMAT,
                "severity": SHELLCHECK_DEFAULT_SEVERITY,
                "exclude": None,
                "shell": None,
            },
            default_timeout=SHELLCHECK_DEFAULT_TIMEOUT,
        )

    def set_options(  # type: ignore[override]
        self,
        severity: str | None = None,
        exclude: list[str] | None = None,
        shell: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Set Shellcheck-specific options.

        Args:
            severity: Minimum severity to report (error, warning, info, style).
            exclude: List of codes to exclude (e.g., ["SC2086", "SC2046"]).
            shell: Force shell dialect (bash, sh, dash, ksh, zsh).
            **kwargs: Other tool options.
        """
        if severity is not None:
            severity = normalize_shellcheck_severity(severity)

        if shell is not None:
            shell = normalize_shellcheck_shell(shell)

        validate_list(exclude, "exclude")
        validate_str(severity, "severity")
        validate_str(shell, "shell")

        options = filter_none_options(
            severity=severity,
            exclude=exclude,
            shell=shell,  # nosec B604 - shell is dialect, not subprocess shell=True
        )
        super().set_options(**options, **kwargs)

    def _build_command(self) -> list[str]:
        """Build the shellcheck command.

        Returns:
            List of command arguments.
        """
        cmd: list[str] = ["shellcheck"]

        # Always use json1 format for reliable parsing
        cmd.extend(["--format", SHELLCHECK_DEFAULT_FORMAT])

        # Add severity option
        severity_opt = self.options.get("severity", SHELLCHECK_DEFAULT_SEVERITY)
        severity = (
            str(severity_opt)
            if severity_opt is not None
            else SHELLCHECK_DEFAULT_SEVERITY
        )
        cmd.extend(["--severity", severity])

        # Add exclude codes
        exclude_opt = self.options.get("exclude")
        if exclude_opt is not None and isinstance(exclude_opt, list):
            for code in exclude_opt:
                cmd.extend(["--exclude", str(code)])

        # Add shell dialect
        shell_opt = self.options.get("shell")
        if shell_opt is not None:
            cmd.extend(["--shell", str(shell_opt)])

        return cmd

    def _process_single_file(
        self,
        file_path: str,
        timeout: int,
        results: dict[str, Any],
    ) -> None:
        """Process a single shell script with shellcheck.

        Args:
            file_path: Path to the shell script to process.
            timeout: Timeout in seconds for the shellcheck command.
            results: Dictionary to accumulate results across files.
        """
        cmd = self._build_command() + [str(file_path)]
        try:
            success, output = self._run_subprocess(cmd=cmd, timeout=timeout)
            issues = parse_shellcheck_output(output=output)
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

    def check(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Check files with Shellcheck.

        Args:
            paths: List of file or directory paths to check.
            options: Runtime options that override defaults.

        Returns:
            ToolResult with check results.
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(paths=paths, options=options)
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        # Shellcheck can process multiple files, but we process one at a time
        # for consistent error handling and progress reporting
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
                    self._process_single_file(
                        file_path=file_path,
                        timeout=ctx.timeout,
                        results=results,
                    )
        else:
            for file_path in shell_files:
                self._process_single_file(
                    file_path=file_path,
                    timeout=ctx.timeout,
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
            success=results["all_success"],
            output=final_output,
            issues_count=results["total_issues"],
            issues=results["all_issues"],
        )

    def fix(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Shellcheck cannot fix issues, only report them.

        Args:
            paths: List of file or directory paths to fix.
            options: Tool-specific options.

        Raises:
            NotImplementedError: Shellcheck does not support fixing issues.
        """
        raise NotImplementedError(
            "Shellcheck cannot automatically fix issues. Run 'lintro check' to see "
            "issues.",
        )
