"""ESLint linter integration."""

import os
import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass, field

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import Tool, ToolConfig, ToolResult
from lintro.parsers.eslint.eslint_issue import EslintIssue
from lintro.parsers.eslint.eslint_parser import parse_eslint_output
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes

# Constants for ESLint configuration
ESLINT_DEFAULT_TIMEOUT: int = 30
ESLINT_DEFAULT_PRIORITY: int = 50  # Lower priority than formatters
ESLINT_FILE_PATTERNS: list[str] = [
    "*.js",
    "*.jsx",
    "*.ts",
    "*.tsx",
    "*.mjs",
    "*.cjs",
]


@dataclass
class EslintTool(BaseTool):
    """ESLint linter integration.

    A linter for JavaScript and TypeScript that identifies problems in code.
    """

    name: str = "eslint"
    description: str = (
        "Linter for JavaScript and TypeScript that identifies and reports "
        "on patterns in code"
    )
    can_fix: bool = True
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=ESLINT_DEFAULT_PRIORITY,  # Lower priority than formatters
            conflicts_with=[],  # No direct conflicts
            file_patterns=ESLINT_FILE_PATTERNS,
            tool_type=ToolType.LINTER,
        ),
    )

    def __post_init__(self) -> None:
        """Initialize eslint tool."""
        super().__post_init__()
        # Note: .eslintignore is handled natively by ESLint
        # ESLint config files (.eslintrc.*, eslint.config.*) are also
        # discovered natively

    def set_options(
        self,
        exclude_patterns: list[str] | None = None,
        include_venv: bool = False,
        timeout: int | None = None,
        verbose_fix_output: bool | None = None,
        **kwargs,
    ) -> None:
        """Set options for the core.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
            timeout: Timeout in seconds per file (default: 30)
            verbose_fix_output: If True, include raw ESLint output in fix()
            **kwargs: Additional options (ignored for compatibility)
        """
        if exclude_patterns is not None:
            self.exclude_patterns = exclude_patterns.copy()
        self.include_venv = include_venv
        if timeout is not None:
            self.timeout = timeout
        if verbose_fix_output is not None:
            self.options["verbose_fix_output"] = verbose_fix_output

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
            f"ESLint execution timed out ({timeout_val}s limit exceeded).\n\n"
            "This may indicate:\n"
            "  - Large codebase taking too long to process\n"
            "  - Need to increase timeout via --tool-options eslint:timeout=N"
        )
        timeout_issue = EslintIssue(
            file="execution",
            line=1,
            code="TIMEOUT",
            message=timeout_msg,
            column=1,
            severity=2,
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
        """Check files with ESLint without making changes.

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
        eslint_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )
        logger.debug(
            f"[EslintTool] Discovered {len(eslint_files)} files matching patterns: "
            f"{self.config.file_patterns}",
        )
        logger.debug(
            f"[EslintTool] Exclude patterns applied: {self.exclude_patterns}",
        )
        if eslint_files:
            logger.debug(
                f"[EslintTool] Files to check (first 10): " f"{eslint_files[:10]}",
            )
        if not eslint_files:
            return Tool.to_result(
                name=self.name,
                success=True,
                output="No files to check.",
                issues_count=0,
            )

        # Use relative paths and set cwd to the common parent
        cwd: str = self.get_cwd(paths=eslint_files)
        logger.debug(f"[EslintTool] Working directory: {cwd}")
        rel_files: list[str] = [
            os.path.relpath(f, cwd) if cwd else f for f in eslint_files
        ]

        # Build ESLint command with JSON output format
        cmd: list[str] = self._get_executable_command(tool_name="eslint") + [
            "--format",
            "json",
        ]

        # Add Lintro config injection args if available
        config_args = self._build_config_args()
        if config_args:
            cmd.extend(config_args)
            logger.debug(
                "[EslintTool] Using Lintro config injection",
            )

        cmd.extend(rel_files)
        logger.debug(f"[EslintTool] Running: {' '.join(cmd)} (cwd={cwd})")
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
        issues: list = parse_eslint_output(output=output)
        issues_count: int = len(issues)
        success: bool = issues_count == 0

        # Standardize: suppress ESLint's informational output when no issues
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
        """Fix auto-fixable issues in files with ESLint.

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
        eslint_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )
        if not eslint_files:
            return Tool.to_result(
                name=self.name,
                success=True,
                output="No files to fix.",
                issues_count=0,
            )

        # First, check for issues before fixing
        cwd: str = self.get_cwd(paths=eslint_files)
        rel_files: list[str] = [
            os.path.relpath(f, cwd) if cwd else f for f in eslint_files
        ]

        # Get Lintro config injection args if available
        config_args = self._build_config_args()

        # Check for issues first
        check_cmd: list[str] = self._get_executable_command(tool_name="eslint") + [
            "--format",
            "json",
        ]
        if config_args:
            check_cmd.extend(config_args)
        check_cmd.extend(rel_files)
        logger.debug(f"[EslintTool] Checking: {' '.join(check_cmd)} (cwd={cwd})")
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
        initial_issues: list = parse_eslint_output(output=check_output)
        initial_count: int = len(initial_issues)

        # Now fix the issues
        fix_cmd: list[str] = self._get_executable_command(tool_name="eslint") + [
            "--fix",
        ]
        if config_args:
            fix_cmd.extend(config_args)
        fix_cmd.extend(rel_files)
        logger.debug(f"[EslintTool] Fixing: {' '.join(fix_cmd)} (cwd={cwd})")
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
        remaining_issues: list = parse_eslint_output(output=final_check_output)
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

        # Combine initial and remaining issues so formatter can split them by fixability
        all_issues = (initial_issues or []) + (remaining_issues or [])

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
