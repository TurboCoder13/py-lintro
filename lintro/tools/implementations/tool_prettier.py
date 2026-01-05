"""Prettier code formatter integration."""

import os
import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig, ToolResult
from lintro.parsers.prettier.prettier_issue import PrettierIssue
from lintro.parsers.prettier.prettier_parser import parse_prettier_output
from lintro.tools.core.tool_base import BaseTool

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
    can_fix: bool = field(default=True)
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=PRETTIER_DEFAULT_PRIORITY,  # High priority
            conflicts_with=[],  # No direct conflicts
            file_patterns=PRETTIER_FILE_PATTERNS,  # Applies to many file types
            tool_type=ToolType.FORMATTER,
        ),
    )

    def __post_init__(self) -> None:
        """Initialize prettier tool."""
        super().__post_init__()
        # Note: .prettierignore is handled by passing --ignore-path to prettier
        # rather than loading into lintro's exclude patterns, to ensure prettier's
        # native ignore logic is used consistently

    def set_options(
        self,
        exclude_patterns: list[str] | None = None,
        include_venv: bool = False,
        timeout: int | None = None,
        verbose_fix_output: bool | None = None,
        line_length: int | None = None,
        **kwargs,
    ) -> None:
        """Set options for the core.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
            timeout: Timeout in seconds per file (default: 30)
            verbose_fix_output: If True, include raw Prettier output in fix()
            line_length: Print width for prettier (maps to --print-width).
                If provided, this will be stored and used in CLI args.
            **kwargs: Additional options (ignored for compatibility)

        Raises:
            ValueError: If line_length is not a positive integer.
        """
        if exclude_patterns is not None:
            self.exclude_patterns = exclude_patterns.copy()
        self.include_venv = include_venv
        if timeout is not None:
            self.timeout = timeout
        if verbose_fix_output is not None:
            self.options["verbose_fix_output"] = verbose_fix_output
        if line_length is not None:
            if not isinstance(line_length, int):
                raise ValueError("line_length must be an integer")
            if line_length <= 0:
                raise ValueError("line_length must be positive")
            self.options["line_length"] = line_length

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

    def _find_prettier_config(self, search_dir: str | None = None) -> str | None:
        """Locate prettier config file by walking up the directory tree.

        Prettier searches upward from the file's directory to find config files,
        so we do the same to match native behavior and ensure config is found
        even when cwd is a subdirectory.

        Args:
            search_dir: Directory to start searching from. If None, searches from
                current working directory.

        Returns:
            str | None: Path to config file if found, None otherwise.
        """
        config_paths = [
            ".prettierrc",
            ".prettierrc.json",
            ".prettierrc.js",
            ".prettierrc.yaml",
            ".prettierrc.yml",
            "prettier.config.js",
            "package.json",
        ]
        # Search upward from search_dir (or cwd) to find config, just like prettier does
        start_dir = os.path.abspath(search_dir) if search_dir else os.getcwd()
        current_dir = start_dir

        # Walk upward from the directory to find config
        # Stop at filesystem root to avoid infinite loop
        while True:
            for config_name in config_paths:
                config_path = os.path.join(current_dir, config_name)
                if os.path.exists(config_path):
                    # For package.json, check if it contains prettier config
                    if config_name == "package.json":
                        try:
                            import json

                            with open(config_path, encoding="utf-8") as f:
                                pkg_data = json.load(f)
                                if "prettier" not in pkg_data:
                                    continue
                        except (
                            json.JSONDecodeError,
                            FileNotFoundError,
                            PermissionError,
                        ):
                            # Skip invalid or unreadable package.json files
                            continue
                    logger.debug(
                        f"[PrettierTool] Found config file: {config_path} "
                        f"(searched from {start_dir})",
                    )
                    return config_path

            # Move up one directory
            parent_dir = os.path.dirname(current_dir)
            # Stop if we've reached the filesystem root (parent == current)
            if parent_dir == current_dir:
                break
            current_dir = parent_dir

        return None

    def _find_prettierignore(self, search_dir: str | None = None) -> str | None:
        """Locate .prettierignore file by walking up the directory tree.

        Prettier searches upward from the file's directory to find .prettierignore,
        so we do the same to match native behavior and ensure ignore file is found
        even when cwd is a subdirectory.

        Args:
            search_dir: Directory to start searching from. If None, searches from
                current working directory.

        Returns:
            str | None: Path to .prettierignore file if found, None otherwise.
        """
        ignore_filename = ".prettierignore"
        # Search upward from search_dir (or cwd) to find ignore file
        start_dir = os.path.abspath(search_dir) if search_dir else os.getcwd()
        current_dir = start_dir

        # Walk upward from the directory to find ignore file
        # Stop at filesystem root to avoid infinite loop
        while True:
            ignore_path = os.path.join(current_dir, ignore_filename)
            if os.path.exists(ignore_path):
                logger.debug(
                    f"[PrettierTool] Found .prettierignore: {ignore_path} "
                    f"(searched from {start_dir})",
                )
                return ignore_path

            # Move up one directory
            parent_dir = os.path.dirname(current_dir)
            # Stop if we've reached the filesystem root (parent == current)
            if parent_dir == current_dir:
                break
            current_dir = parent_dir

        return None

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
            f"Prettier execution timed out ({timeout_val}s limit exceeded).\n\n"
            "This may indicate:\n"
            "  - Large codebase taking too long to process\n"
            "  - Need to increase timeout via --tool-options prettier:timeout=N"
        )
        timeout_issue = PrettierIssue(
            file="execution",
            line=0,
            code="TIMEOUT",
            message=timeout_msg,
            column=0,
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
        """Check files with Prettier without making changes.

        Args:
            paths: List of file or directory paths to check

        Returns:
            ToolResult instance
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(
            paths,
            default_timeout=PRETTIER_DEFAULT_TIMEOUT,
        )
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        logger.debug(
            f"[PrettierTool] Discovered {len(ctx.files)} files matching patterns: "
            f"{self.config.file_patterns}",
        )
        logger.debug(
            f"[PrettierTool] Exclude patterns applied: {self.exclude_patterns}",
        )
        if ctx.files:
            logger.debug(
                f"[PrettierTool] Files to check (first 10): {ctx.files[:10]}",
            )
        logger.debug(f"[PrettierTool] Working directory: {ctx.cwd}")

        # Resolve executable in a manner consistent with other tools
        cmd: list[str] = self._get_executable_command(tool_name="prettier") + [
            "--check",
        ]

        # Add Lintro config injection args (--no-config, --config)
        # This takes precedence over native config auto-discovery
        config_args = self._build_config_args()
        if config_args:
            cmd.extend(config_args)
            logger.debug(
                "[PrettierTool] Using Lintro config injection",
            )
        else:
            # Fallback: Find config and ignore files by walking up from cwd
            found_config = self._find_prettier_config(search_dir=ctx.cwd)
            if found_config:
                logger.debug(
                    f"[PrettierTool] Found config: {found_config} (auto-detecting)",
                )
            else:
                logger.debug(
                    "[PrettierTool] No prettier config file found (using defaults)",
                )
                # Apply line_length as --print-width if set and no config found
                line_length = self.options.get("line_length")
                if line_length:
                    cmd.extend(["--print-width", str(line_length)])
                    logger.debug(
                        "[PrettierTool] Using --print-width=%s from options",
                        line_length,
                    )
            # Find .prettierignore by walking up from cwd
            prettierignore_path = self._find_prettierignore(search_dir=ctx.cwd)
            if prettierignore_path:
                logger.debug(
                    f"[PrettierTool] Found .prettierignore: {prettierignore_path} "
                    "(auto-detecting)",
                )

        cmd.extend(ctx.rel_files)
        logger.debug(f"[PrettierTool] Running: {' '.join(cmd)} (cwd={ctx.cwd})")
        try:
            result = self._run_subprocess(
                cmd=cmd,
                timeout=ctx.timeout,
                cwd=ctx.cwd,
            )
        except subprocess.TimeoutExpired:
            return self._create_timeout_result(timeout_val=ctx.timeout)
        output: str = result[1]
        # Do not filter lines post-hoc; rely on discovery and ignore files
        issues: list[Any] = parse_prettier_output(output=output)
        issues_count: int = len(issues)
        success: bool = issues_count == 0
        # Standardize: suppress Prettier's informational output when no issues
        # so the unified logger prints a single, consistent success line.
        if success:
            output = None

        # Return full ToolResult so table rendering can use parsed issues
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
        """Format files with Prettier.

        Args:
            paths: List of file or directory paths to format

        Returns:
            ToolResult: Result object with counts and messages.
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(
            paths,
            no_files_message="No files to format.",
            default_timeout=PRETTIER_DEFAULT_TIMEOUT,
        )
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        # Get Lintro config injection args (--no-config, --config)
        config_args = self._build_config_args()
        fallback_args: list[str] = []
        if not config_args:
            # Fallback: Find config and ignore files by walking up from cwd
            found_config = self._find_prettier_config(search_dir=ctx.cwd)
            if found_config:
                logger.debug(
                    f"[PrettierTool] Found config: {found_config} (auto-detecting)",
                )
            else:
                logger.debug(
                    "[PrettierTool] No prettier config file found (using defaults)",
                )
                # Apply line_length as --print-width if set and no config found
                line_length = self.options.get("line_length")
                if line_length:
                    fallback_args.extend(["--print-width", str(line_length)])
                    logger.debug(
                        "[PrettierTool] Using --print-width=%s from options",
                        line_length,
                    )
            prettierignore_path = self._find_prettierignore(search_dir=ctx.cwd)
            if prettierignore_path:
                logger.debug(
                    f"[PrettierTool] Found .prettierignore: {prettierignore_path} "
                    "(auto-detecting)",
                )

        # Check for issues first
        check_cmd: list[str] = self._get_executable_command(tool_name="prettier") + [
            "--check",
        ]
        # Add Lintro config injection if available, otherwise use fallback args
        if config_args:
            check_cmd.extend(config_args)
        elif fallback_args:
            check_cmd.extend(fallback_args)
        check_cmd.extend(ctx.rel_files)
        logger.debug(f"[PrettierTool] Checking: {' '.join(check_cmd)} (cwd={ctx.cwd})")
        try:
            check_result = self._run_subprocess(
                cmd=check_cmd,
                timeout=ctx.timeout,
                cwd=ctx.cwd,
            )
        except subprocess.TimeoutExpired:
            return self._create_timeout_result(timeout_val=ctx.timeout)
        check_output: str = check_result[1]

        # Parse initial issues
        initial_issues: list[Any] = parse_prettier_output(output=check_output)
        initial_count: int = len(initial_issues)

        # Now fix the issues
        fix_cmd: list[str] = self._get_executable_command(tool_name="prettier") + [
            "--write",
        ]
        # Add Lintro config injection if available, otherwise use fallback args
        if config_args:
            fix_cmd.extend(config_args)
        elif fallback_args:
            fix_cmd.extend(fallback_args)
        fix_cmd.extend(ctx.rel_files)
        logger.debug(f"[PrettierTool] Fixing: {' '.join(fix_cmd)} (cwd={ctx.cwd})")
        try:
            fix_result = self._run_subprocess(
                cmd=fix_cmd,
                timeout=ctx.timeout,
                cwd=ctx.cwd,
            )
        except subprocess.TimeoutExpired:
            return self._create_timeout_result(
                timeout_val=ctx.timeout,
                initial_issues=initial_issues,
                initial_count=initial_count,
            )
        fix_output: str = fix_result[1]

        # Check for remaining issues after fixing
        try:
            final_check_result = self._run_subprocess(
                cmd=check_cmd,
                timeout=ctx.timeout,
                cwd=ctx.cwd,
            )
        except subprocess.TimeoutExpired:
            return self._create_timeout_result(
                timeout_val=ctx.timeout,
                initial_issues=initial_issues,
                initial_count=initial_count,
            )
        final_check_output: str = final_check_result[1]
        remaining_issues: list[Any] = parse_prettier_output(output=final_check_output)
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
