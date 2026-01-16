"""SQLFluff tool definition.

SQLFluff is a SQL linter and formatter with support for many SQL dialects.
It parses SQL into an AST and performs linting rules on top of it.
"""

from __future__ import annotations

import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass
from typing import Any

import click

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.sqlfluff.sqlfluff_parser import parse_sqlfluff_output
from lintro.plugins.base import BaseToolPlugin
from lintro.plugins.protocol import ToolDefinition
from lintro.plugins.registry import register_tool
from lintro.tools.core.option_validators import (
    filter_none_options,
    validate_list,
    validate_str,
)

# Constants for SQLFluff configuration
SQLFLUFF_DEFAULT_TIMEOUT: int = 60
SQLFLUFF_DEFAULT_PRIORITY: int = 50
SQLFLUFF_FILE_PATTERNS: list[str] = ["*.sql"]
SQLFLUFF_DEFAULT_FORMAT: str = "json"


@register_tool
@dataclass
class SqlfluffPlugin(BaseToolPlugin):
    """SQLFluff SQL linter and formatter plugin.

    This plugin integrates SQLFluff with Lintro for linting and formatting
    SQL files.
    """

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition.

        Returns:
            ToolDefinition containing tool metadata.
        """
        return ToolDefinition(
            name="sqlfluff",
            description="SQL linter and formatter with dialect support",
            can_fix=True,
            tool_type=ToolType.LINTER | ToolType.FORMATTER,
            file_patterns=SQLFLUFF_FILE_PATTERNS,
            priority=SQLFLUFF_DEFAULT_PRIORITY,
            conflicts_with=[],
            native_configs=[".sqlfluff", "pyproject.toml"],
            version_command=["sqlfluff", "--version"],
            min_version="3.0.0",
            default_options={
                "timeout": SQLFLUFF_DEFAULT_TIMEOUT,
                "dialect": None,
                "exclude_rules": None,
                "rules": None,
                "templater": None,
            },
            default_timeout=SQLFLUFF_DEFAULT_TIMEOUT,
        )

    def set_options(  # type: ignore[override]
        self,
        dialect: str | None = None,
        exclude_rules: list[str] | None = None,
        rules: list[str] | None = None,
        templater: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Set SQLFluff-specific options.

        Args:
            dialect: SQL dialect (ansi, bigquery, postgres, mysql, snowflake,
                sqlite, etc.).
            exclude_rules: List of rules to exclude.
            rules: List of rules to include.
            templater: Templater to use (raw, jinja, python, placeholder).
            **kwargs: Other tool options.
        """
        validate_str(dialect, "dialect")
        validate_list(exclude_rules, "exclude_rules")
        validate_list(rules, "rules")
        validate_str(templater, "templater")

        options = filter_none_options(
            dialect=dialect,
            exclude_rules=exclude_rules,
            rules=rules,
            templater=templater,
        )
        super().set_options(**options, **kwargs)

    def _build_lint_command(self, files: list[str]) -> list[str]:
        """Build the sqlfluff lint command.

        Args:
            files: List of files to lint.

        Returns:
            List of command arguments.
        """
        cmd: list[str] = ["sqlfluff", "lint", "--format", SQLFLUFF_DEFAULT_FORMAT]

        # Add dialect option
        dialect_opt = self.options.get("dialect")
        if dialect_opt is not None:
            cmd.extend(["--dialect", str(dialect_opt)])

        # Add exclude rules
        exclude_rules_opt = self.options.get("exclude_rules")
        if exclude_rules_opt is not None and isinstance(exclude_rules_opt, list):
            for rule in exclude_rules_opt:
                cmd.extend(["--exclude-rules", str(rule)])

        # Add rules
        rules_opt = self.options.get("rules")
        if rules_opt is not None and isinstance(rules_opt, list):
            for rule in rules_opt:
                cmd.extend(["--rules", str(rule)])

        # Add templater
        templater_opt = self.options.get("templater")
        if templater_opt is not None:
            cmd.extend(["--templater", str(templater_opt)])

        # Add files
        cmd.extend(files)

        return cmd

    def _build_fix_command(self, files: list[str]) -> list[str]:
        """Build the sqlfluff fix command.

        Args:
            files: List of files to fix.

        Returns:
            List of command arguments.
        """
        cmd: list[str] = ["sqlfluff", "fix", "--force"]

        # Add dialect option
        dialect_opt = self.options.get("dialect")
        if dialect_opt is not None:
            cmd.extend(["--dialect", str(dialect_opt)])

        # Add exclude rules
        exclude_rules_opt = self.options.get("exclude_rules")
        if exclude_rules_opt is not None and isinstance(exclude_rules_opt, list):
            for rule in exclude_rules_opt:
                cmd.extend(["--exclude-rules", str(rule)])

        # Add rules
        rules_opt = self.options.get("rules")
        if rules_opt is not None and isinstance(rules_opt, list):
            for rule in rules_opt:
                cmd.extend(["--rules", str(rule)])

        # Add templater
        templater_opt = self.options.get("templater")
        if templater_opt is not None:
            cmd.extend(["--templater", str(templater_opt)])

        # Add files
        cmd.extend(files)

        return cmd

    def _process_single_file_check(
        self,
        file_path: str,
        timeout: int,
        results: dict[str, Any],
    ) -> None:
        """Process a single SQL file with sqlfluff lint.

        Args:
            file_path: Path to the SQL file to process.
            timeout: Timeout in seconds for the sqlfluff command.
            results: Dictionary to accumulate results across files.
        """
        cmd = self._build_lint_command(files=[str(file_path)])
        try:
            success, output = self._run_subprocess(cmd=cmd, timeout=timeout)
            issues = parse_sqlfluff_output(output=output)
            issues_count = len(issues)

            if not success and issues_count == 0:
                # Tool failure without parseable issues
                results["all_success"] = False
            if issues_count > 0:
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
        results: dict[str, Any],
    ) -> None:
        """Process a single SQL file with sqlfluff fix.

        Args:
            file_path: Path to the SQL file to fix.
            timeout: Timeout in seconds for the sqlfluff command.
            results: Dictionary to accumulate results across files.
        """
        cmd = self._build_fix_command(files=[str(file_path)])
        try:
            success, output = self._run_subprocess(cmd=cmd, timeout=timeout)

            if not success:
                results["all_success"] = False

            if output.strip():
                results["all_outputs"].append(output)
        except subprocess.TimeoutExpired:
            results["skipped_files"].append(file_path)
            results["all_success"] = False
            results["execution_failures"] += 1
        except (OSError, ValueError, RuntimeError) as e:
            results["all_outputs"].append(f"Error processing {file_path}: {e!s}")
            results["all_success"] = False
            results["execution_failures"] += 1

    def check(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Check files with SQLFluff.

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

        sql_files = ctx.files

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
        if len(sql_files) >= 2:
            with click.progressbar(
                sql_files,
                label="Processing files",
                bar_template="%(label)s  %(info)s",
            ) as bar:
                for file_path in bar:
                    self._process_single_file_check(file_path, ctx.timeout, results)
        else:
            for file_path in sql_files:
                self._process_single_file_check(file_path, ctx.timeout, results)

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
        """Fix issues in files with SQLFluff.

        Args:
            paths: List of file or directory paths to fix.
            options: Runtime options that override defaults.

        Returns:
            ToolResult with fix results.
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(paths, options)
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        sql_files = ctx.files

        # Accumulate results across all files
        results: dict[str, Any] = {
            "all_outputs": [],
            "all_success": True,
            "skipped_files": [],
            "execution_failures": 0,
        }

        # Show progress bar only when processing multiple files
        if len(sql_files) >= 2:
            with click.progressbar(
                sql_files,
                label="Fixing files",
                bar_template="%(label)s  %(info)s",
            ) as bar:
                for file_path in bar:
                    self._process_single_file_fix(file_path, ctx.timeout, results)
        else:
            for file_path in sql_files:
                self._process_single_file_fix(file_path, ctx.timeout, results)

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
            issues_count=0,
            issues=[],
        )
