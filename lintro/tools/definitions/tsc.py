"""Tsc (TypeScript Compiler) tool definition.

Tsc is the TypeScript compiler which performs static type checking on
TypeScript files. It helps catch type-related bugs before runtime by
analyzing type annotations and inferences.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass
from typing import Any

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.tsc.tsc_parser import parse_tsc_output
from lintro.plugins.base import BaseToolPlugin
from lintro.plugins.protocol import ToolDefinition
from lintro.plugins.registry import register_tool
from lintro.tools.core.timeout_utils import create_timeout_result

# Constants for Tsc configuration
TSC_DEFAULT_TIMEOUT: int = 60
TSC_DEFAULT_PRIORITY: int = 82  # Same as mypy (type checkers)
TSC_FILE_PATTERNS: list[str] = ["*.ts", "*.tsx", "*.mts", "*.cts"]


@register_tool
@dataclass
class TscPlugin(BaseToolPlugin):
    """TypeScript Compiler (tsc) type checking plugin.

    This plugin integrates the TypeScript compiler with Lintro for static
    type checking of TypeScript files.
    """

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition.

        Returns:
            ToolDefinition containing tool metadata.
        """
        return ToolDefinition(
            name="tsc",
            description="TypeScript compiler for static type checking",
            can_fix=False,
            tool_type=ToolType.LINTER | ToolType.TYPE_CHECKER,
            file_patterns=TSC_FILE_PATTERNS,
            priority=TSC_DEFAULT_PRIORITY,
            conflicts_with=[],
            native_configs=["tsconfig.json"],
            version_command=["tsc", "--version"],
            min_version="4.0.0",
            default_options={
                "timeout": TSC_DEFAULT_TIMEOUT,
                "project": None,
                "strict": None,
                "skip_lib_check": True,
            },
            default_timeout=TSC_DEFAULT_TIMEOUT,
        )

    def set_options(  # type: ignore[override]
        self,
        project: str | None = None,
        strict: bool | None = None,
        skip_lib_check: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Set tsc-specific options.

        Args:
            project: Path to tsconfig.json file.
            strict: Enable strict type checking mode.
            skip_lib_check: Skip type checking of declaration files (default: True).
            **kwargs: Other tool options.

        Raises:
            ValueError: If any provided option is of an unexpected type.
        """
        if project is not None and not isinstance(project, str):
            raise ValueError("project must be a string path")
        if strict is not None and not isinstance(strict, bool):
            raise ValueError("strict must be a boolean")
        if skip_lib_check is not None and not isinstance(skip_lib_check, bool):
            raise ValueError("skip_lib_check must be a boolean")

        options: dict[str, object] = {
            "project": project,
            "strict": strict,
            "skip_lib_check": skip_lib_check,
        }
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _get_tsc_command(self) -> list[str]:
        """Get the command to run tsc.

        Prefers direct tsc executable, falls back to bunx/npx.

        Returns:
            Command arguments for tsc.
        """
        # Prefer direct executable if available
        if shutil.which("tsc"):
            return ["tsc"]
        # Try bunx (bun) - note: bunx tsc works if typescript is installed
        if shutil.which("bunx"):
            return ["bunx", "tsc"]
        # Try npx (npm)
        if shutil.which("npx"):
            return ["npx", "tsc"]
        # Last resort - hope tsc is in PATH
        return ["tsc"]

    def _build_command(self, files: list[str]) -> list[str]:
        """Build the tsc invocation command.

        Args:
            files: Relative file paths that should be checked by tsc.
                   Note: When using --project, files are determined by tsconfig.json.

        Returns:
            A list of command arguments ready to be executed.
        """
        cmd: list[str] = self._get_tsc_command()

        # Core flags for linting (no output, machine-readable format)
        cmd.extend(["--noEmit", "--pretty", "false"])

        # Project flag (uses tsconfig.json)
        project_opt = self.options.get("project")
        if project_opt:
            cmd.extend(["--project", str(project_opt)])
        else:
            # If no explicit project, tsc will look for tsconfig.json in cwd
            # We don't pass files when tsconfig.json exists (tsc uses its config)
            pass

        # Strict mode override
        if self.options.get("strict") is True:
            cmd.append("--strict")
        elif self.options.get("strict") is False:
            cmd.append("--noStrict")

        # Skip lib check (faster, avoids issues with node_modules types)
        if self.options.get("skip_lib_check", True):
            cmd.append("--skipLibCheck")

        # Only pass files if no project/tsconfig is being used
        # When tsconfig.json is present, tsc determines files from it
        if not project_opt and files:
            # Check if tsconfig.json exists in cwd (tsc will use it automatically)
            # In this case, we don't pass files
            cmd.extend(files)

        return cmd

    def check(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Check files with tsc.

        Args:
            paths: List of file or directory paths to check.
            options: Runtime options that override defaults.

        Returns:
            ToolResult with check results.
        """
        # Merge runtime options
        merged_options = dict(self.options)
        merged_options.update(options)

        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(
            paths,
            merged_options,
            no_files_message="No TypeScript files to check.",
        )

        if ctx.should_skip and ctx.early_result is not None:
            return ctx.early_result

        # Safety check: if should_skip but no early_result, create one
        if ctx.should_skip:
            return ToolResult(
                name=self.definition.name,
                success=True,
                output="No TypeScript files to check.",
                issues_count=0,
            )

        logger.debug("[tsc] Discovered {} TypeScript file(s)", len(ctx.files))

        # Build command
        cmd = self._build_command(files=ctx.rel_files)
        logger.debug("[tsc] Running with cwd={} and cmd={}", ctx.cwd, cmd)

        try:
            success, output = self._run_subprocess(
                cmd=cmd,
                timeout=ctx.timeout,
                cwd=ctx.cwd,
            )
        except subprocess.TimeoutExpired:
            timeout_result = create_timeout_result(
                tool=self,
                timeout=ctx.timeout,
                cmd=cmd,
            )
            return ToolResult(
                name=self.definition.name,
                success=timeout_result.success,
                output=timeout_result.output,
                issues_count=timeout_result.issues_count,
                issues=timeout_result.issues,
            )

        # Parse output
        issues = parse_tsc_output(output=output)
        issues_count = len(issues)

        if not success and issues_count == 0:
            # Execution failed but no structured issues were parsed
            return ToolResult(
                name=self.definition.name,
                success=False,
                output=output or "tsc execution failed.",
                issues_count=0,
            )

        return ToolResult(
            name=self.definition.name,
            success=issues_count == 0,
            output=None,
            issues_count=issues_count,
            issues=issues,
        )

    def fix(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Tsc does not support auto-fixing.

        Args:
            paths: Paths or files passed for completeness.
            options: Runtime options (unused).

        Raises:
            NotImplementedError: Always, because tsc cannot fix issues.
        """
        raise NotImplementedError(
            "Tsc cannot automatically fix issues. Type errors require "
            "manual code changes.",
        )
