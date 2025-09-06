"""Prettier code formatter integration."""

import os
from dataclasses import dataclass, field

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import Tool, ToolConfig, ToolResult
from lintro.parsers.prettier.prettier_parser import parse_prettier_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes

# Constants for Prettier configuration
PRETTIER_DEFAULT_TIMEOUT: int = 30
PRETTIER_DEFAULT_PRIORITY: int = 80
PRETTIER_FILE_PATTERNS: list[str] = [
    "*.js",
    "*.jsx",
    "*.ts",
    "*.tsx",
    "*.css",
    "*.scss",
    "*.less",
    "*.html",
    "*.json",
    "*.yaml",
    "*.yml",
    "*.md",
    "*.graphql",
    "*.vue",
]


@dataclass
class PrettierTool(BaseTool):
    """Prettier code formatter integration.

    A code formatter that supports multiple languages (JavaScript, TypeScript,
    CSS, HTML, etc.).
    """

    name: str = "prettier"
    description: str = (
        "Code formatter that supports multiple languages (JavaScript, TypeScript, "
        "CSS, HTML, etc.)"
    )
    can_fix: bool = True
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=PRETTIER_DEFAULT_PRIORITY,  # High priority
            conflicts_with=[],  # No direct conflicts
            file_patterns=PRETTIER_FILE_PATTERNS,  # Applies to many file types
            tool_type=ToolType.FORMATTER,
        ),
    )

    def set_options(
        self,
        exclude_patterns: list[str] | None = None,
        include_venv: bool = False,
        timeout: int | None = None,
        verbose_fix_output: bool | None = None,
    ) -> None:
        """Set options for the core.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
            timeout: Timeout in seconds per file (default: 30)
            verbose_fix_output: If True, include raw Prettier output in fix()
        """
        self.exclude_patterns = exclude_patterns or []
        self.include_venv = include_venv
        if timeout is not None:
            self.timeout = timeout
        if verbose_fix_output is not None:
            self.options["verbose_fix_output"] = verbose_fix_output

    def _find_config(self) -> str | None:
        """Locate a Prettier config if none is found by native discovery.

        Wrapper-first default: rely on Prettier's native discovery via cwd. Only
        return a config path if we later decide to ship a default config and the
        user has no config present. For now, return None to avoid forcing config.

        Returns:
            str | None: Path to a discovered configuration file, or None if
            no explicit configuration should be enforced.
        """
        return None

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files with Prettier without making changes.

        Args:
            paths: List of file or directory paths to check

        Returns:
            ToolResult instance
        """
        self._validate_paths(paths=paths)
        prettier_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )
        if not prettier_files:
            return Tool.to_result(
                name=self.name,
                success=True,
                output="No files to check.",
                issues_count=0,
            )
        # Use relative paths and set cwd to the common parent
        cwd: str = self.get_cwd(paths=prettier_files)
        rel_files: list[str] = [
            os.path.relpath(f, cwd) if cwd else f for f in prettier_files
        ]
        # Resolve executable in a manner consistent with other tools
        cmd: list[str] = self._get_executable_command(tool_name="prettier") + [
            "--check",
        ]
        # Do not force config; rely on native discovery via cwd
        cmd.extend(rel_files)
        logger.debug(f"[PrettierTool] Running: {' '.join(cmd)} (cwd={cwd})")
        result = self._run_subprocess(
            cmd=cmd,
            timeout=self.options.get("timeout", self._default_timeout),
            cwd=cwd,
        )
        output: str = result[1]
        # Do not filter lines post-hoc; rely on discovery and ignore files
        issues: list = parse_prettier_output(output=output)
        issues_count: int = len(issues)
        success: bool = issues_count == 0
        # Standardize: suppress Prettier's informational output when no issues
        # so the unified logger prints a single, consistent success line.
        if success:
            output = None
        return Tool.to_result(
            name=self.name,
            success=success,
            output=output,
            issues_count=issues_count,
        )

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Format files with Prettier.

        Args:
            paths: List of file or directory paths to format

        Returns:
            ToolResult: Result object with counts and messages.
        """
        self._validate_paths(paths=paths)
        prettier_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )
        if not prettier_files:
            return Tool.to_result(
                name=self.name,
                success=True,
                output="No files to format.",
                issues_count=0,
            )

        # First, check for issues before fixing
        cwd: str = self.get_cwd(paths=prettier_files)
        rel_files: list[str] = [
            os.path.relpath(f, cwd) if cwd else f for f in prettier_files
        ]

        # Check for issues first
        check_cmd: list[str] = self._get_executable_command(tool_name="prettier") + [
            "--check",
        ]
        # Do not force config; rely on native discovery via cwd
        check_cmd.extend(rel_files)
        logger.debug(f"[PrettierTool] Checking: {' '.join(check_cmd)} (cwd={cwd})")
        check_result = self._run_subprocess(
            cmd=check_cmd,
            timeout=self.options.get("timeout", self._default_timeout),
            cwd=cwd,
        )
        check_output: str = check_result[1]

        # Parse initial issues
        initial_issues: list = parse_prettier_output(output=check_output)
        initial_count: int = len(initial_issues)

        # Now fix the issues
        fix_cmd: list[str] = self._get_executable_command(tool_name="prettier") + [
            "--write",
        ]
        fix_cmd.extend(rel_files)
        logger.debug(f"[PrettierTool] Fixing: {' '.join(fix_cmd)} (cwd={cwd})")
        fix_result = self._run_subprocess(
            cmd=fix_cmd,
            timeout=self.options.get("timeout", self._default_timeout),
            cwd=cwd,
        )
        fix_output: str = fix_result[1]

        # Check for remaining issues after fixing
        final_check_result = self._run_subprocess(
            cmd=check_cmd,
            timeout=self.options.get("timeout", self._default_timeout),
            cwd=cwd,
        )
        final_check_output: str = final_check_result[1]
        remaining_issues: list = parse_prettier_output(output=final_check_output)
        remaining_count: int = len(remaining_issues)

        # Calculate fixed issues
        fixed_count: int = max(0, initial_count - remaining_count)

        # Build output message
        output_lines: list[str] = []
        if fixed_count > 0:
            output_lines.append(f"Fixed {fixed_count} formatting issue(s)")

        if remaining_count > 0:
            output_lines.append(
                f"Found {remaining_count} issue(s) that cannot be auto-fixed",
            )
            for issue in remaining_issues[:5]:
                output_lines.append(f"  {issue.file} - {issue.message}")
            if len(remaining_issues) > 5:
                output_lines.append(f"  ... and {len(remaining_issues) - 5} more")

        # If there were no initial issues, rely on the logger's unified
        # success line (avoid duplicate "No issues found" lines here)
        elif remaining_count == 0 and fixed_count > 0:
            output_lines.append("All formatting issues were successfully auto-fixed")

        # Add verbose raw formatting output only when explicitly requested
        if (
            self.options.get("verbose_fix_output", False)
            and fix_output
            and fix_output.strip()
        ):
            output_lines.append(f"Formatting output:\n{fix_output}")

        final_output: str | None = "\n".join(output_lines) if output_lines else None

        # Success means no remaining issues
        success: bool = remaining_count == 0

        return ToolResult(
            name=self.name,
            success=success,
            output=final_output,
            # For fix operations, issues_count represents remaining for summaries
            issues_count=remaining_count,
            initial_issues_count=initial_count,
            fixed_issues_count=fixed_count,
            remaining_issues_count=remaining_count,
        )
