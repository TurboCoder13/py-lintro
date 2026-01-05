"""Actionlint integration for lintro.

This module wires the `actionlint` CLI into Lintro's tool system. It discovers
GitHub Actions workflow files, executes `actionlint`, parses its output into
structured issues, and returns a normalized `ToolResult`.
"""

from __future__ import annotations

import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass, field
from typing import Any

import click
from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_config import ToolConfig
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.actionlint.actionlint_parser import parse_actionlint_output
from lintro.tools.core.tool_base import BaseTool

# Defaults
ACTIONLINT_DEFAULT_TIMEOUT: int = 30
ACTIONLINT_DEFAULT_PRIORITY: int = 40
ACTIONLINT_FILE_PATTERNS: list[str] = ["*.yml", "*.yaml"]


@dataclass
class ActionlintTool(BaseTool):
    """GitHub Actions workflow linter (actionlint).

    Attributes:
        name: Tool name used across the system.
        description: Human-readable description for listings/help.
        can_fix: Whether the tool can apply fixes (actionlint cannot).
        config: `ToolConfig` with defaults for priority, file patterns, and
            `ToolType` classification.
    """

    name: str = field(default="actionlint")
    description: str = field(default="Static checker for GitHub Actions workflows")
    can_fix: bool = field(default=False)
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=ACTIONLINT_DEFAULT_PRIORITY,
            conflicts_with=[],
            file_patterns=ACTIONLINT_FILE_PATTERNS,
            tool_type=ToolType.LINTER | ToolType.INFRASTRUCTURE,
            options={
                "timeout": ACTIONLINT_DEFAULT_TIMEOUT,
                # Option placeholders for future extension (e.g., color, format)
            },
        ),
    )

    def _build_command(self) -> list[str]:
        """Build the base actionlint command.

        We intentionally avoid flags here for maximum portability across
        platforms and actionlint versions. The tool's default text output
        follows the conventional ``file:line:col: message [CODE]`` format,
        which our parser handles directly without requiring a custom format
        switch.

        Returns:
            The base command list for invoking actionlint.
        """
        return ["actionlint"]

    def _process_single_file(
        self,
        file_path: str,
        timeout: int,
        results: dict,
    ) -> None:
        """Process a single file with actionlint.

        Args:
            file_path: Path to the file to process.
            timeout: Timeout in seconds.
            results: Mutable dict to accumulate results.
        """
        cmd = self._build_command() + [file_path]
        try:
            success, output = self._run_subprocess(cmd=cmd, timeout=timeout)
            issues = parse_actionlint_output(output)

            if not success:
                results["all_success"] = False
            if output and (issues or not success):
                results["all_outputs"].append(output)
            if issues:
                results["all_issues"].extend(issues)
        except subprocess.TimeoutExpired:
            results["skipped_files"].append(file_path)
            results["all_success"] = False
            results["execution_failures"] += 1
        except Exception as e:  # pragma: no cover
            results["all_success"] = False
            results["all_outputs"].append(f"Error checking {file_path}: {e}")
            results["execution_failures"] += 1

    def check(self, paths: list[str]) -> ToolResult:
        """Check GitHub Actions workflow files with actionlint.

        Args:
            paths: File or directory paths to search for workflow files.

        Returns:
            A `ToolResult` containing success status, aggregated output (if any),
            issue count, and parsed issues.
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(
            paths,
            default_timeout=ACTIONLINT_DEFAULT_TIMEOUT,
        )
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        # Restrict to GitHub Actions workflow location
        workflow_files: list[str] = [
            f for f in ctx.files if "/.github/workflows/" in f.replace("\\", "/")
        ]
        logger.debug(f"Files to check (actionlint): {workflow_files}")

        if not workflow_files:
            return ToolResult(
                name=self.name,
                success=True,
                output="No GitHub workflow files found to check.",
                issues_count=0,
            )

        # Accumulate results across all files
        results: dict[str, Any] = {
            "all_outputs": [],
            "all_issues": [],
            "all_success": True,
            "skipped_files": [],
            "execution_failures": 0,
        }

        # Show progress bar only when processing multiple files
        if len(workflow_files) >= 2:
            with click.progressbar(
                workflow_files,
                label="Processing files",
                bar_template="%(label)s  %(info)s",
            ) as bar:
                for file_path in bar:
                    self._process_single_file(file_path, ctx.timeout, results)
        else:
            for file_path in workflow_files:
                self._process_single_file(file_path, ctx.timeout, results)

        # Build combined output
        combined_output = (
            "\n".join(results["all_outputs"]) if results["all_outputs"] else None
        )
        if results["skipped_files"]:
            timeout_msg = (
                f"Skipped {len(results['skipped_files'])} file(s) due to timeout "
                f"({ctx.timeout}s limit exceeded):"
            )
            for file in results["skipped_files"]:
                timeout_msg += f"\n  - {file}"
            combined_output = (
                f"{combined_output}\n\n{timeout_msg}"
                if combined_output
                else timeout_msg
            )

        non_timeout_failures = results["execution_failures"] - len(
            results["skipped_files"],
        )
        if non_timeout_failures > 0:
            failure_msg = (
                f"Failed to process {non_timeout_failures} file(s) "
                "due to execution errors"
            )
            combined_output = (
                f"{combined_output}\n\n{failure_msg}"
                if combined_output
                else failure_msg
            )

        return ToolResult(
            name=self.name,
            success=results["all_success"],
            output=combined_output,
            issues_count=len(results["all_issues"]),
            issues=results["all_issues"],
        )

    def fix(self, paths: list[str]) -> ToolResult:
        """Raise since actionlint cannot apply automatic fixes.

        Args:
            paths: File or directory paths (ignored).

        Raises:
            NotImplementedError: Actionlint does not support auto-fixing.
        """
        raise NotImplementedError("actionlint cannot automatically fix issues.")
