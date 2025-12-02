"""Prettier code formatter integration."""

import os
import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass, field

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import Tool, ToolConfig, ToolResult
from lintro.parsers.prettier.prettier_issue import PrettierIssue
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
    ) -> None:
        """Set options for the core.

        Args:
            exclude_patterns: List of patterns to exclude
            include_venv: Whether to include virtual environment directories
            timeout: Timeout in seconds per file (default: 30)
            verbose_fix_output: If True, include raw Prettier output in fix()
        """
        if exclude_patterns is not None:
            self.exclude_patterns = exclude_patterns.copy()
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
            line=None,
            code="TIMEOUT",
            message=timeout_msg,
            column=None,
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
        # Check version requirements
        version_result = self._verify_tool_version()
        if version_result is not None:
            return version_result

        self._validate_paths(paths=paths)
        prettier_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )
        logger.debug(
            f"[PrettierTool] Discovered {len(prettier_files)} files matching patterns: "
            f"{self.config.file_patterns}",
        )
        logger.debug(
            f"[PrettierTool] Exclude patterns applied: {self.exclude_patterns}",
        )
        if prettier_files:
            logger.debug(
                f"[PrettierTool] Files to check (first 10): " f"{prettier_files[:10]}",
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
        logger.debug(f"[PrettierTool] Working directory: {cwd}")
        rel_files: list[str] = [
            os.path.relpath(f, cwd) if cwd else f for f in prettier_files
        ]
        # Resolve executable in a manner consistent with other tools
        cmd: list[str] = self._get_executable_command(tool_name="prettier") + [
            "--check",
        ]
        # Find config and ignore files by walking up from cwd to repo root
        # This ensures they're found even when cwd is a subdirectory
        found_config = self._find_prettier_config(search_dir=cwd)
        if found_config:
            # Let prettier auto-detect config for consistent behavior
            # cmd.extend(["--config", found_config])
            logger.debug(
                f"[PrettierTool] Found config file: {found_config} (auto-detecting)",
            )
        else:
            logger.debug(
                "[PrettierTool] No prettier config file found (using defaults)",
            )
        # Find .prettierignore by walking up from cwd
        prettierignore_path = self._find_prettierignore(search_dir=cwd)
        if prettierignore_path:
            # Let prettier auto-detect ignore file for consistent behavior
            # cmd.extend(["--ignore-path", prettierignore_path])
            logger.debug(
                f"[PrettierTool] Found .prettierignore: {prettierignore_path} "
                "(auto-detecting)",
            )
        cmd.extend(rel_files)
        logger.debug(f"[PrettierTool] Running: {' '.join(cmd)} (cwd={cwd})")
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
        # Do not filter lines post-hoc; rely on discovery and ignore files
        issues: list = parse_prettier_output(output=output)
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
        # Check version requirements
        version_result = self._verify_tool_version()
        if version_result is not None:
            return version_result

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

        # Find config and ignore files by walking up from cwd to repo root
        self._find_prettier_config(search_dir=cwd)
        self._find_prettierignore(search_dir=cwd)

        # Check for issues first
        check_cmd: list[str] = self._get_executable_command(tool_name="prettier") + [
            "--check",
        ]
        # Let prettier auto-detect config and ignore files for consistent behavior
        # if found_config:
        #     check_cmd.extend(["--config", found_config])
        # if prettierignore_path:
        #     check_cmd.extend(["--ignore-path", prettierignore_path])
        check_cmd.extend(rel_files)
        logger.debug(f"[PrettierTool] Checking: {' '.join(check_cmd)} (cwd={cwd})")
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
        initial_issues: list = parse_prettier_output(output=check_output)
        initial_count: int = len(initial_issues)

        # Now fix the issues
        fix_cmd: list[str] = self._get_executable_command(tool_name="prettier") + [
            "--write",
        ]
        # Let prettier auto-detect config and ignore files for consistent behavior
        # if found_config:
        #     fix_cmd.extend(["--config", found_config])
        # if prettierignore_path:
        #     fix_cmd.extend(["--ignore-path", prettierignore_path])
        fix_cmd.extend(rel_files)
        logger.debug(f"[PrettierTool] Fixing: {' '.join(fix_cmd)} (cwd={cwd})")
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
