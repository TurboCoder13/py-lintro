"""Biome linter integration."""

import os
import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass, field

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import Tool, ToolConfig, ToolResult
from lintro.parsers.biome.biome_issue import BiomeIssue
from lintro.parsers.biome.biome_parser import parse_biome_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.path_filtering import walk_files_with_excludes

# Constants for Biome configuration
BIOME_DEFAULT_TIMEOUT: int = 30
BIOME_DEFAULT_PRIORITY: int = 50
BIOME_FILE_PATTERNS: list[str] = [
    "*.js",
    "*.jsx",
    "*.ts",
    "*.tsx",
    "*.mjs",
    "*.cjs",
    "*.json",
    "*.css",
]


@dataclass
class BiomeTool(BaseTool):
    """Biome linter integration.

    A fast linter for JavaScript, TypeScript, JSON, and CSS.
    """

    name: str = field(default="biome")
    description: str = field(
        default="Fast linter for JavaScript, TypeScript, JSON, and CSS that "
        "provides detailed diagnostics and safe fixes",
    )
    can_fix: bool = field(default=True)
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=BIOME_DEFAULT_PRIORITY,
            conflicts_with=[],  # No direct conflicts
            file_patterns=BIOME_FILE_PATTERNS,
            tool_type=ToolType.LINTER,
        ),
    )

    def __post_init__(self) -> None:
        """Initialize biome tool."""
        super().__post_init__()
        # Enable VCS ignore by default to respect .gitignore patterns
        self.options.setdefault("use_vcs_ignore", True)
        # Note: Biome config files (.biome.json, biome.jsonc) are also
        # discovered natively

    def set_options(
        self,
        exclude_patterns: list[str] | None = None,
        include_venv: bool = False,
        timeout: int | None = None,
        verbose_fix_output: bool | None = None,
        use_vcs_ignore: bool | None = None,
        **kwargs,
    ) -> None:
        """Set options for the tool.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
            timeout: Timeout in seconds per file (default: 30)
            verbose_fix_output: If True, include raw Biome output in fix()
            use_vcs_ignore: If True, use VCS ignore file (.gitignore) to exclude files
            **kwargs: Additional options (ignored for compatibility)
        """
        if exclude_patterns is not None:
            self.exclude_patterns = exclude_patterns.copy()
        self.include_venv = include_venv
        if timeout is not None:
            self.options["timeout"] = timeout
        if verbose_fix_output is not None:
            self.options["verbose_fix_output"] = verbose_fix_output
        if use_vcs_ignore is not None:
            self.options["use_vcs_ignore"] = use_vcs_ignore

    def _create_timeout_result(
        self,
        timeout_val: int,
        initial_issues: list | None = None,
        initial_count: int = 0,
    ) -> ToolResult:
        """Create a ToolResult for timeout scenarios.

        Args:
            timeout_val: The timeout value that was exceeded.
            initial_issues: Optional list of issues found before timeout.
            initial_count: Optional count of initial issues.

        Returns:
            ToolResult: ToolResult instance representing timeout failure.
        """
        timeout_msg = (
            f"Biome execution timed out ({timeout_val}s limit exceeded).\n\n"
            "This may indicate:\n"
            "  - Large codebase taking too long to process\n"
            "  - Need to increase timeout via --tool-options biome:timeout=N"
        )
        timeout_issue = BiomeIssue(
            file="execution",
            line=1,
            column=1,
            code="TIMEOUT",
            message=timeout_msg,
            severity="error",
            fixable=False,
        )
        combined_issues = (initial_issues or []) + [timeout_issue]
        return ToolResult(
            name=self.name,
            success=False,
            output=timeout_msg,
            issues_count=len(combined_issues),
            issues=combined_issues,
            initial_issues_count=initial_count,
            fixed_issues_count=0,
            remaining_issues_count=len(combined_issues),
        )

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files with Biome without making changes.

        Args:
            paths: List of file or directory paths to check

        Returns:
            ToolResult instance
        """
        # Check version requirements
        version_result = self._verify_tool_version()
        if version_result is not None:
            return version_result

        self._validate_paths(paths=paths)
        biome_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )
        logger.debug(
            f"[BiomeTool] Discovered {len(biome_files)} files matching patterns: "
            f"{self.config.file_patterns}",
        )
        logger.debug(
            f"[BiomeTool] Exclude patterns applied: {self.exclude_patterns}",
        )
        if biome_files:
            logger.debug(
                f"[BiomeTool] Files to check (first 10): {biome_files[:10]}",
            )
        if not biome_files:
            return Tool.to_result(
                name=self.name,
                success=True,
                output="No files to check.",
                issues_count=0,
            )

        # Use relative paths and set cwd to the common parent
        cwd: str = self.get_cwd(paths=biome_files)
        logger.debug(f"[BiomeTool] Working directory: {cwd}")
        rel_files: list[str] = [
            os.path.relpath(f, cwd) if cwd else f for f in biome_files
        ]

        # Build Biome command with JSON reporter
        cmd: list[str] = self._get_executable_command(tool_name="biome") + [
            "lint",
            "--reporter",
            "json",
        ]

        # Add Lintro config injection args if available
        config_args = self._build_config_args()
        if config_args:
            cmd.extend(config_args)
            logger.debug(
                "[BiomeTool] Using Lintro config injection",
            )

        # Add VCS ignore option if enabled
        if self.options.get("use_vcs_ignore", False):
            cmd.extend(["--vcs-use-ignore-file", "true"])
            logger.debug("[BiomeTool] Using VCS ignore file")

        cmd.extend(rel_files)
        logger.debug(f"[BiomeTool] Running: {' '.join(cmd)} (cwd={cwd})")
        timeout_val: int = self.options.get("timeout", self._default_timeout)
        try:
            result = self._run_subprocess(
                cmd=cmd,
                timeout=timeout_val,
                cwd=cwd,
            )
        except subprocess.TimeoutExpired:
            return self._create_timeout_result(timeout_val=timeout_val)
        output: str = result[1]
        issues: list = parse_biome_output(output=output)
        issues_count: int = len(issues)
        success: bool = issues_count == 0

        # Standardize: suppress Biome's informational output when no issues
        # so the unified logger prints a single, consistent success line.
        if success:
            output = None

        return ToolResult(
            name=self.name,
            success=success,
            output=output,
            issues_count=issues_count,
            issues=issues,
        )

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Fix auto-fixable issues in files with Biome.

        Args:
            paths: List of file or directory paths to fix

        Returns:
            ToolResult: Result object with counts and messages.
        """
        # Check version requirements
        version_result = self._verify_tool_version()
        if version_result is not None:
            return version_result

        self._validate_paths(paths=paths)
        biome_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )
        if not biome_files:
            return Tool.to_result(
                name=self.name,
                success=True,
                output="No files to fix.",
                issues_count=0,
            )

        # First, check for issues before fixing
        cwd: str = self.get_cwd(paths=biome_files)
        rel_files: list[str] = [
            os.path.relpath(f, cwd) if cwd else f for f in biome_files
        ]

        # Get Lintro config injection args if available
        config_args = self._build_config_args()

        # Check for issues first
        check_cmd: list[str] = self._get_executable_command(tool_name="biome") + [
            "lint",
            "--reporter",
            "json",
        ]
        if config_args:
            check_cmd.extend(config_args)
        # Add VCS ignore option if enabled
        if self.options.get("use_vcs_ignore", False):
            check_cmd.extend(["--vcs-use-ignore-file", "true"])
        check_cmd.extend(rel_files)
        logger.debug(f"[BiomeTool] Checking: {' '.join(check_cmd)} (cwd={cwd})")
        timeout_val: int = self.options.get("timeout", self._default_timeout)
        try:
            check_result = self._run_subprocess(
                cmd=check_cmd,
                timeout=timeout_val,
                cwd=cwd,
            )
        except subprocess.TimeoutExpired:
            return self._create_timeout_result(timeout_val=timeout_val)
        check_output: str = check_result[1]

        # Parse initial issues
        initial_issues: list = parse_biome_output(output=check_output)
        initial_count: int = len(initial_issues)

        # Now fix the issues
        fix_cmd: list[str] = self._get_executable_command(tool_name="biome") + [
            "lint",
            "--write",
        ]
        if config_args:
            fix_cmd.extend(config_args)
        # Add VCS ignore option if enabled
        if self.options.get("use_vcs_ignore", False):
            fix_cmd.extend(["--vcs-use-ignore-file", "true"])
        fix_cmd.extend(rel_files)
        logger.debug(f"[BiomeTool] Fixing: {' '.join(fix_cmd)} (cwd={cwd})")
        try:
            fix_result = self._run_subprocess(
                cmd=fix_cmd,
                timeout=timeout_val,
                cwd=cwd,
            )
        except subprocess.TimeoutExpired:
            return self._create_timeout_result(
                timeout_val=timeout_val,
                initial_issues=initial_issues,
                initial_count=initial_count,
            )
        fix_output: str = fix_result[1]

        # Check for remaining issues after fixing
        try:
            final_check_result = self._run_subprocess(
                cmd=check_cmd,
                timeout=timeout_val,
                cwd=cwd,
            )
        except subprocess.TimeoutExpired:
            return self._create_timeout_result(
                timeout_val=timeout_val,
                initial_issues=initial_issues,
                initial_count=initial_count,
            )
        final_check_output: str = final_check_result[1]
        remaining_issues: list = parse_biome_output(output=final_check_output)
        remaining_count: int = len(remaining_issues)

        # Calculate fixed issues
        fixed_count: int = max(0, initial_count - remaining_count)

        # Build output message
        output_lines: list[str] = []
        if fixed_count > 0:
            output_lines.append(f"Fixed {fixed_count} issue(s)")

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
            output_lines.append("All issues were successfully auto-fixed")

        # Add verbose raw fix output only when explicitly requested
        if (
            self.options.get("verbose_fix_output", False)
            and fix_output
            and fix_output.strip()
        ):
            output_lines.append(f"Fix output:\n{fix_output}")

        final_output: str | None = "\n".join(output_lines) if output_lines else None

        # Success means no remaining issues
        success: bool = remaining_count == 0

        # Use only remaining issues (post-fix list) to avoid duplicates
        # The formatter relies on metadata counters (initial_issues_count,
        # fixed_issues_count, remaining_issues_count) for summaries
        all_issues = remaining_issues or []

        return ToolResult(
            name=self.name,
            success=success,
            output=final_output,
            # For fix operations, issues_count represents remaining for summaries
            issues_count=remaining_count,
            # Provide both initial (fixed) and remaining issues for display
            issues=all_issues,
            initial_issues_count=initial_count,
            fixed_issues_count=fixed_count,
            remaining_issues_count=remaining_count,
        )
