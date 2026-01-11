"""Hadolint tool definition.

Hadolint is a Dockerfile linter that helps you build best practice Docker images.
It parses the Dockerfile into an AST and performs rules on top of the AST.
It also uses ShellCheck to lint the Bash code inside RUN instructions.
"""

from __future__ import annotations

import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass
from typing import Any

import click

from lintro.enums.hadolint_enums import (
    HadolintFailureThreshold,
    HadolintFormat,
    normalize_hadolint_format,
    normalize_hadolint_threshold,
)
from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.hadolint.hadolint_parser import parse_hadolint_output
from lintro.plugins.base import BaseToolPlugin
from lintro.plugins.protocol import ToolDefinition
from lintro.plugins.registry import register_tool
from lintro.tools.core.option_validators import (
    filter_none_options,
    validate_bool,
    validate_list,
)

# Constants for Hadolint configuration
HADOLINT_DEFAULT_TIMEOUT: int = 30
HADOLINT_DEFAULT_PRIORITY: int = 50
HADOLINT_FILE_PATTERNS: list[str] = ["Dockerfile", "Dockerfile.*"]
HADOLINT_DEFAULT_FORMAT: str = "tty"
HADOLINT_DEFAULT_FAILURE_THRESHOLD: str = "info"
HADOLINT_DEFAULT_NO_COLOR: bool = True


@register_tool
@dataclass
class HadolintPlugin(BaseToolPlugin):
    """Hadolint Dockerfile linter plugin.

    This plugin integrates Hadolint with Lintro for checking Dockerfiles
    against best practices.
    """

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition.

        Returns:
            ToolDefinition containing tool metadata.
        """
        return ToolDefinition(
            name="hadolint",
            description=(
                "Dockerfile linter that helps you build best practice Docker images"
            ),
            can_fix=False,
            tool_type=ToolType.LINTER | ToolType.INFRASTRUCTURE,
            file_patterns=HADOLINT_FILE_PATTERNS,
            priority=HADOLINT_DEFAULT_PRIORITY,
            conflicts_with=[],
            native_configs=[".hadolint.yaml", ".hadolint.yml"],
            version_command=["hadolint", "--version"],
            min_version="2.12.0",
            default_options={
                "timeout": HADOLINT_DEFAULT_TIMEOUT,
                "format": HADOLINT_DEFAULT_FORMAT,
                "failure_threshold": HADOLINT_DEFAULT_FAILURE_THRESHOLD,
                "ignore": None,
                "trusted_registries": None,
                "require_labels": None,
                "strict_labels": False,
                "no_fail": False,
                "no_color": HADOLINT_DEFAULT_NO_COLOR,
            },
            default_timeout=HADOLINT_DEFAULT_TIMEOUT,
        )

    def set_options(  # type: ignore[override]
        self,
        format: str | HadolintFormat | None = None,
        failure_threshold: str | HadolintFailureThreshold | None = None,
        ignore: list[str] | None = None,
        trusted_registries: list[str] | None = None,
        require_labels: list[str] | None = None,
        strict_labels: bool | None = None,
        no_fail: bool | None = None,
        no_color: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Set Hadolint-specific options.

        Args:
            format: Output format (tty, json, checkstyle, codeclimate, etc.).
            failure_threshold: Exit with failure only when rules with
                severity >= threshold.
            ignore: List of rule codes to ignore (e.g., ['DL3006', 'SC2086']).
            trusted_registries: List of trusted Docker registries.
            require_labels: List of required labels with schemas.
            strict_labels: Whether to use strict label checking.
            no_fail: Whether to suppress exit codes.
            no_color: Whether to disable color output.
            **kwargs: Other tool options.
        """
        if format is not None:
            fmt_enum = normalize_hadolint_format(format)
            format = fmt_enum.name.lower()

        if failure_threshold is not None:
            thr_enum = normalize_hadolint_threshold(failure_threshold)
            failure_threshold = thr_enum.name.lower()

        validate_list(ignore, "ignore")
        validate_list(trusted_registries, "trusted_registries")
        validate_list(require_labels, "require_labels")
        validate_bool(strict_labels, "strict_labels")
        validate_bool(no_fail, "no_fail")
        validate_bool(no_color, "no_color")

        options = filter_none_options(
            format=format,
            failure_threshold=failure_threshold,
            ignore=ignore,
            trusted_registries=trusted_registries,
            require_labels=require_labels,
            strict_labels=strict_labels,
            no_fail=no_fail,
            no_color=no_color,
        )
        super().set_options(**options, **kwargs)

    def _build_command(self) -> list[str]:
        """Build the hadolint command.

        Returns:
            List of command arguments.
        """
        cmd: list[str] = ["hadolint"]

        # Add format option
        format_opt = self.options.get("format", HADOLINT_DEFAULT_FORMAT)
        format_option = (
            str(format_opt) if format_opt is not None else HADOLINT_DEFAULT_FORMAT
        )
        cmd.extend(["--format", format_option])

        # Add failure threshold
        threshold_opt = self.options.get(
            "failure_threshold",
            HADOLINT_DEFAULT_FAILURE_THRESHOLD,
        )
        failure_threshold = (
            str(threshold_opt)
            if threshold_opt is not None
            else HADOLINT_DEFAULT_FAILURE_THRESHOLD
        )
        cmd.extend(["--failure-threshold", failure_threshold])

        # Add ignore rules
        ignore_opt = self.options.get("ignore")
        if ignore_opt is not None and isinstance(ignore_opt, list):
            for rule in ignore_opt:
                cmd.extend(["--ignore", str(rule)])

        # Add trusted registries
        registries_opt = self.options.get("trusted_registries")
        if registries_opt is not None and isinstance(registries_opt, list):
            for registry in registries_opt:
                cmd.extend(["--trusted-registry", str(registry)])

        # Add required labels
        labels_opt = self.options.get("require_labels")
        if labels_opt is not None and isinstance(labels_opt, list):
            for label in labels_opt:
                cmd.extend(["--require-label", str(label)])

        # Add strict labels
        if self.options.get("strict_labels", False):
            cmd.append("--strict-labels")

        # Add no-fail option
        if self.options.get("no_fail", False):
            cmd.append("--no-fail")

        # Add no-color option (default to True for better parsing)
        if self.options.get("no_color", HADOLINT_DEFAULT_NO_COLOR):
            cmd.append("--no-color")

        return cmd

    def _process_single_file(
        self,
        file_path: str,
        timeout: int,
        results: dict[str, Any],
    ) -> None:
        """Process a single Dockerfile with hadolint.

        Args:
            file_path: Path to the Dockerfile to process.
            timeout: Timeout in seconds for the hadolint command.
            results: Dictionary to accumulate results across files.
        """
        cmd = self._build_command() + [str(file_path)]
        try:
            success, output = self._run_subprocess(cmd=cmd, timeout=timeout)
            issues = parse_hadolint_output(output=output)
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
        """Check files with Hadolint.

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

        # Hadolint processes files one at a time (doesn't support batch mode)
        dockerfile_files = ctx.files

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
        if len(dockerfile_files) >= 2:
            with click.progressbar(
                dockerfile_files,
                label="Processing files",
                bar_template="%(label)s  %(info)s",
            ) as bar:
                for file_path in bar:
                    self._process_single_file(file_path, ctx.timeout, results)
        else:
            for file_path in dockerfile_files:
                self._process_single_file(file_path, ctx.timeout, results)

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
        """Hadolint cannot fix issues, only report them.

        Args:
            paths: List of file or directory paths to fix.
            options: Tool-specific options.

        Raises:
            NotImplementedError: Hadolint does not support fixing issues.
        """
        raise NotImplementedError(
            "Hadolint cannot automatically fix issues. Run 'lintro check' to see "
            "issues.",
        )
