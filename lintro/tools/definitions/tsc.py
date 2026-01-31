"""Tsc (TypeScript Compiler) tool definition.

Tsc is the TypeScript compiler which performs static type checking on
TypeScript files. It helps catch type-related bugs before runtime by
analyzing type annotations and inferences.

File Targeting Behavior:
    By default, lintro respects your file selection even when tsconfig.json exists.
    This is achieved by creating a temporary tsconfig that extends your project's
    config but overrides the `include` pattern to target only the specified files.

    To use native tsconfig.json file selection instead, set `use_project_files=True`.

Example:
    # Check only specific files (default behavior)
    lintro check src/utils.ts --tools tsc

    # Check all files defined in tsconfig.json
    lintro check . --tools tsc --tool-options "tsc:use_project_files=True"
"""

from __future__ import annotations

import json
import shutil
import subprocess  # nosec B404 - used safely with shell disabled
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

from loguru import logger

from lintro._tool_versions import get_min_version
from lintro.enums.tool_name import ToolName
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
            min_version=get_min_version(ToolName.TSC),
            default_options={
                "timeout": TSC_DEFAULT_TIMEOUT,
                "project": None,
                "strict": None,
                "skip_lib_check": True,
                "use_project_files": False,
            },
            default_timeout=TSC_DEFAULT_TIMEOUT,
        )

    def set_options(  # type: ignore[override]
        self,
        project: str | None = None,
        strict: bool | None = None,
        skip_lib_check: bool | None = None,
        use_project_files: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Set tsc-specific options.

        Args:
            project: Path to tsconfig.json file.
            strict: Enable strict type checking mode.
            skip_lib_check: Skip type checking of declaration files (default: True).
            use_project_files: When True, use tsconfig.json's include/files patterns
                instead of lintro's file targeting. Default is False, meaning lintro
                respects your file selection even when tsconfig.json exists.
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
        if use_project_files is not None and not isinstance(use_project_files, bool):
            raise ValueError("use_project_files must be a boolean")

        options: dict[str, object] = {
            "project": project,
            "strict": strict,
            "skip_lib_check": skip_lib_check,
            "use_project_files": use_project_files,
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

    def _find_tsconfig(self, cwd: Path) -> Path | None:
        """Find tsconfig.json in the working directory or via project option.

        Args:
            cwd: Working directory to search for tsconfig.json.

        Returns:
            Path to tsconfig.json if found, None otherwise.
        """
        # Check explicit project option first
        project_opt = self.options.get("project")
        if project_opt and isinstance(project_opt, str):
            project_path = Path(project_opt)
            if project_path.is_absolute():
                return project_path if project_path.exists() else None
            resolved = cwd / project_path
            return resolved if resolved.exists() else None

        # Check for tsconfig.json in cwd
        tsconfig = cwd / "tsconfig.json"
        return tsconfig if tsconfig.exists() else None

    def _create_temp_tsconfig(
        self,
        base_tsconfig: Path,
        files: list[str],
        cwd: Path,
    ) -> Path:
        """Create a temporary tsconfig.json that extends the base config.

        This allows lintro to respect user file selection while preserving
        all compiler options from the project's tsconfig.json.

        Args:
            base_tsconfig: Path to the original tsconfig.json to extend.
            files: List of file paths to include (relative to cwd).
            cwd: Working directory for resolving paths.

        Returns:
            Path to the temporary tsconfig.json file.

        Raises:
            OSError: If the temporary file cannot be created or written.
        """
        # Use absolute path for extends since temp file is in system temp dir.
        # This avoids permission issues in Docker containers where cwd may be
        # a read-only volume mount.
        abs_base = base_tsconfig.resolve()

        # Convert relative file paths to absolute paths since the temp tsconfig
        # will be in a different directory
        abs_files = [str((cwd / f).resolve()) for f in files]

        temp_config = {
            "extends": str(abs_base),
            "include": abs_files,
            "exclude": [],
            "compilerOptions": {
                # Ensure noEmit is set (type checking only)
                "noEmit": True,
            },
        }

        # Create temp file in system temp directory to avoid permission issues
        # in Docker containers with mounted volumes
        fd, temp_path = tempfile.mkstemp(
            suffix=".json",
            prefix="lintro-tsc-",
        )
        try:
            with open(fd, "w", encoding="utf-8") as f:
                json.dump(temp_config, f, indent=2)
        except OSError:
            # Clean up on failure
            Path(temp_path).unlink(missing_ok=True)
            raise

        logger.debug(
            "[tsc] Created temp tsconfig at {} extending {} with {} files",
            temp_path,
            abs_base,
            len(files),
        )
        return Path(temp_path)

    def _build_command(
        self,
        files: list[str],
        project_path: str | Path | None = None,
        options: dict[str, object] | None = None,
    ) -> list[str]:
        """Build the tsc invocation command.

        Args:
            files: Relative file paths (used only when no project config).
            project_path: Path to tsconfig.json to use (temp or user-specified).
            options: Options dict to use for flags. Defaults to self.options.

        Returns:
            A list of command arguments ready to be executed.
        """
        if options is None:
            options = self.options

        cmd: list[str] = self._get_tsc_command()

        # Core flags for linting (no output, machine-readable format)
        cmd.extend(["--noEmit", "--pretty", "false"])

        # Project flag (uses tsconfig.json - either temp, explicit, or auto-discovered)
        if project_path:
            cmd.extend(["--project", str(project_path)])

        # Strict mode override (--strict is off by default, no flag needed for False)
        if options.get("strict") is True:
            cmd.append("--strict")

        # Skip lib check (faster, avoids issues with node_modules types)
        if options.get("skip_lib_check", True):
            cmd.append("--skipLibCheck")

        # Only pass files directly if no project config is being used
        if not project_path and files:
            cmd.extend(files)

        return cmd

    def check(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Check files with tsc.

        By default, lintro respects your file selection even when tsconfig.json exists.
        This is achieved by creating a temporary tsconfig that extends your project's
        config but targets only the specified files.

        To use native tsconfig.json file selection instead, set use_project_files=True.

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

        # Determine project configuration strategy
        cwd_path = Path(ctx.cwd) if ctx.cwd else Path.cwd()
        use_project_files = merged_options.get("use_project_files", False)
        explicit_project_opt = merged_options.get("project")
        explicit_project = str(explicit_project_opt) if explicit_project_opt else None
        temp_tsconfig: Path | None = None
        project_path: str | None = None

        try:
            # Find existing tsconfig.json
            base_tsconfig = self._find_tsconfig(cwd_path)

            if use_project_files or explicit_project:
                # Native mode: use tsconfig.json as-is for file selection
                # or explicit project path was provided
                project_path = explicit_project or (
                    str(base_tsconfig) if base_tsconfig else None
                )
                logger.debug(
                    "[tsc] Using native tsconfig file selection: {}",
                    project_path,
                )
            elif base_tsconfig:
                # Lintro mode: create temp tsconfig to respect file targeting
                # while preserving compiler options from the project's config
                temp_tsconfig = self._create_temp_tsconfig(
                    base_tsconfig=base_tsconfig,
                    files=ctx.rel_files,
                    cwd=cwd_path,
                )
                project_path = str(temp_tsconfig)
                logger.debug(
                    "[tsc] Using temp tsconfig for file targeting: {}",
                    project_path,
                )
            else:
                # No tsconfig.json found - pass files directly
                project_path = None
                logger.debug("[tsc] No tsconfig.json found, passing files directly")

            # Build command
            cmd = self._build_command(
                files=ctx.rel_files if not project_path else [],
                project_path=project_path,
                options=merged_options,
            )
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
        finally:
            # Clean up temp tsconfig
            if temp_tsconfig and temp_tsconfig.exists():
                try:
                    temp_tsconfig.unlink()
                    logger.debug("[tsc] Cleaned up temp tsconfig: {}", temp_tsconfig)
                except OSError as e:
                    logger.warning("[tsc] Failed to clean up temp tsconfig: {}", e)

    def fix(self, paths: list[str], options: dict[str, object]) -> NoReturn:
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
