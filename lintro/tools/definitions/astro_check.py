"""Astro check tool definition.

Astro check is Astro's built-in type checking command that provides TypeScript
diagnostics for `.astro` files including frontmatter scripts, component props,
and template expressions.

Example:
    # Check Astro project
    lintro check src/ --tools astro-check

    # Check with specific root
    lintro check . --tools astro-check --tool-options "astro-check:root=./packages/web"
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

from loguru import logger

from lintro._tool_versions import get_min_version
from lintro.enums.tool_name import ToolName
from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.astro_check.astro_check_parser import parse_astro_check_output
from lintro.parsers.base_parser import strip_ansi_codes
from lintro.plugins.base import BaseToolPlugin
from lintro.plugins.protocol import ToolDefinition
from lintro.plugins.registry import register_tool
from lintro.tools.core.timeout_utils import create_timeout_result

# Constants for Astro check configuration
ASTRO_CHECK_DEFAULT_TIMEOUT: int = 120
ASTRO_CHECK_DEFAULT_PRIORITY: int = 83  # After tsc (82)
ASTRO_CHECK_FILE_PATTERNS: list[str] = ["*.astro"]


@register_tool
@dataclass
class AstroCheckPlugin(BaseToolPlugin):
    """Astro check type checking plugin.

    This plugin integrates the Astro check command with Lintro for static
    type checking of Astro components.
    """

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition.

        Returns:
            ToolDefinition containing tool metadata.
        """
        return ToolDefinition(
            name="astro-check",
            description="Astro type checker for Astro component diagnostics",
            can_fix=False,
            tool_type=ToolType.LINTER | ToolType.TYPE_CHECKER,
            file_patterns=ASTRO_CHECK_FILE_PATTERNS,
            priority=ASTRO_CHECK_DEFAULT_PRIORITY,
            conflicts_with=[],
            native_configs=[
                "astro.config.mjs",
                "astro.config.ts",
                "astro.config.js",
                "astro.config.cjs",
            ],
            version_command=["astro", "--version"],
            min_version=get_min_version(ToolName.ASTRO_CHECK),
            default_options={
                "timeout": ASTRO_CHECK_DEFAULT_TIMEOUT,
                "root": None,
            },
            default_timeout=ASTRO_CHECK_DEFAULT_TIMEOUT,
        )

    def set_options(  # type: ignore[override]
        self,
        root: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Set astro-check-specific options.

        Args:
            root: Root directory for the Astro project.
            **kwargs: Other tool options.

        Raises:
            ValueError: If any provided option is of an unexpected type.
        """
        if root is not None and not isinstance(root, str):
            raise ValueError("root must be a string path")

        options: dict[str, object] = {"root": root}
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _get_astro_command(self) -> list[str]:
        """Get the command to run astro check.

        Prefers direct astro executable, falls back to bunx/npx.

        Returns:
            Command arguments for astro check.
        """
        # Prefer direct executable if available
        if shutil.which("astro"):
            return ["astro", "check"]
        # Try bunx (bun)
        if shutil.which("bunx"):
            return ["bunx", "astro", "check"]
        # Try npx (npm)
        if shutil.which("npx"):
            return ["npx", "astro", "check"]
        # Last resort
        return ["astro", "check"]

    def _find_astro_config(self, cwd: Path) -> Path | None:
        """Find astro config file in the working directory.

        Args:
            cwd: Working directory to search for config.

        Returns:
            Path to astro config if found, None otherwise.
        """
        config_names = [
            "astro.config.mjs",
            "astro.config.ts",
            "astro.config.js",
            "astro.config.cjs",
        ]
        for config_name in config_names:
            config_path = cwd / config_name
            if config_path.exists():
                return config_path
        return None

    def _build_command(
        self,
        options: dict[str, object] | None = None,
    ) -> list[str]:
        """Build the astro check invocation command.

        Args:
            options: Options dict to use for flags. Defaults to self.options.

        Returns:
            A list of command arguments ready to be executed.
        """
        if options is None:
            options = self.options

        cmd: list[str] = self._get_astro_command()

        # Root directory option
        root = options.get("root")
        if root:
            cmd.extend(["--root", str(root)])

        return cmd

    def check(self, paths: list[str], options: dict[str, object]) -> ToolResult:
        """Check files with astro check.

        Astro check runs on the entire project and uses the project's
        astro.config and tsconfig.json for configuration.

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
            no_files_message="No Astro files to check.",
        )

        if ctx.should_skip and ctx.early_result is not None:
            return ctx.early_result

        # Safety check: if should_skip but no early_result, create one
        if ctx.should_skip:
            return ToolResult(
                name=self.definition.name,
                success=True,
                output="No Astro files to check.",
                issues_count=0,
            )

        logger.debug("[astro-check] Discovered {} Astro file(s)", len(ctx.files))

        # Honor the "root" option if provided, otherwise use ctx.cwd
        root_opt = merged_options.get("root")
        if root_opt and isinstance(root_opt, str):
            cwd_path = Path(root_opt)
            if not cwd_path.is_absolute():
                # Resolve relative to ctx.cwd
                base = Path(ctx.cwd) if ctx.cwd else Path.cwd()
                cwd_path = (base / cwd_path).resolve()
        else:
            cwd_path = Path(ctx.cwd) if ctx.cwd else Path.cwd()

        # Check if astro config exists
        astro_config = self._find_astro_config(cwd_path)
        if not astro_config:
            return ToolResult(
                name=self.definition.name,
                success=True,
                output="No Astro config found. Skipping astro check.",
                issues_count=0,
            )

        # Check if auto-install is enabled
        auto_install = merged_options.get("auto_install", False)
        if auto_install:
            from lintro.utils.node_deps import install_node_deps, should_install_deps

            if should_install_deps(cwd_path):
                logger.info("[astro-check] Auto-installing Node.js dependencies...")
                success, install_output = install_node_deps(cwd_path)
                if not success:
                    return ToolResult(
                        name=self.definition.name,
                        success=False,
                        output=(
                            f"Failed to install Node.js dependencies:\n"
                            f"{install_output}"
                        ),
                        issues_count=0,
                    )
                logger.info("[astro-check] Dependencies installed successfully")

        # Build command
        cmd = self._build_command(options=merged_options)
        logger.debug("[astro-check] Running with cwd={} and cmd={}", cwd_path, cmd)

        try:
            success, output = self._run_subprocess(
                cmd=cmd,
                timeout=ctx.timeout,
                cwd=str(cwd_path),
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
        except FileNotFoundError as e:
            return ToolResult(
                name=self.definition.name,
                success=False,
                output=f"Astro not found: {e}\n\n"
                "Please ensure astro is installed:\n"
                "  - Run 'bun add astro' or 'npm install astro'\n"
                "  - Or install globally: 'bun add -g astro'",
                issues_count=0,
            )
        except OSError as e:
            logger.error("[astro-check] Failed to run astro check: {}", e)
            return ToolResult(
                name=self.definition.name,
                success=False,
                output="astro check execution failed: " + str(e),
                issues_count=0,
            )

        # Parse output
        all_issues = parse_astro_check_output(output=output or "")
        issues_count = len(all_issues)

        # Normalize output for fallback analysis
        normalized_output = strip_ansi_codes(output) if output else ""

        # Handle dependency errors
        if not success and issues_count == 0 and normalized_output:
            if (
                "Cannot find module" in normalized_output
                or "Cannot find type definition" in normalized_output
            ):
                helpful_output = (
                    f"Astro check configuration error:\n{normalized_output}\n\n"
                    "This usually means dependencies aren't installed.\n"
                    "Suggestions:\n"
                    "  - Run 'bun install' or 'npm install' in your project\n"
                    "  - Use '--auto-install' flag to auto-install dependencies"
                )
                return ToolResult(
                    name=self.definition.name,
                    success=False,
                    output=helpful_output,
                    issues_count=0,
                )

            # Generic failure
            return ToolResult(
                name=self.definition.name,
                success=False,
                output=normalized_output or "astro check execution failed.",
                issues_count=0,
            )

        if not success and issues_count == 0:
            return ToolResult(
                name=self.definition.name,
                success=False,
                output="astro check execution failed.",
                issues_count=0,
            )

        return ToolResult(
            name=self.definition.name,
            success=issues_count == 0,
            output=None,
            issues_count=issues_count,
            issues=all_issues,
        )

    def fix(self, paths: list[str], options: dict[str, object]) -> NoReturn:
        """Astro check does not support auto-fixing.

        Args:
            paths: Paths or files passed for completeness.
            options: Runtime options (unused).

        Raises:
            NotImplementedError: Always, because astro check cannot fix issues.
        """
        raise NotImplementedError(
            "Astro check cannot automatically fix issues. Type errors require "
            "manual code changes.",
        )
