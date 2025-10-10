"""Ruff Python linter and formatter integration."""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool import ToolConfig, ToolResult
from lintro.parsers.ruff.ruff_issue import RuffFormatIssue
from lintro.parsers.ruff.ruff_parser import (
    parse_ruff_format_check_output,
    parse_ruff_output,
)
from lintro.tools.core.tool_base import BaseTool
from lintro.utils.tool_utils import walk_files_with_excludes

# Constants for Ruff configuration
RUFF_DEFAULT_TIMEOUT: int = 30
RUFF_DEFAULT_PRIORITY: int = 85
RUFF_FILE_PATTERNS: list[str] = ["*.py", "*.pyi"]
RUFF_OUTPUT_FORMAT: str = "json"
RUFF_TEST_MODE_ENV: str = "LINTRO_TEST_MODE"
RUFF_TEST_MODE_VALUE: str = "1"
DEFAULT_REMAINING_ISSUES_DISPLAY: int = 5


def _load_ruff_config() -> dict:
    """Load ruff configuration from pyproject.toml.

    Returns:
        dict: Ruff configuration dictionary.
    """
    config: dict = {}
    pyproject_path = Path("pyproject.toml")

    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)
                if "tool" in pyproject_data and "ruff" in pyproject_data["tool"]:
                    config = pyproject_data["tool"]["ruff"]
        except Exception as e:
            logger.warning(f"Failed to load ruff configuration: {e}")

    return config


def _load_lintro_ignore() -> list[str]:
    """Load patterns from .lintro-ignore file.

    Returns:
        list[str]: List of ignore patterns.
    """
    ignore_patterns: list[str] = []
    lintro_ignore_path = Path(".lintro-ignore")

    if lintro_ignore_path.exists():
        try:
            with open(lintro_ignore_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        ignore_patterns.append(line)
        except Exception as e:
            logger.warning(f"Failed to load .lintro-ignore: {e}")

    return ignore_patterns


@dataclass
class RuffTool(BaseTool):
    """Ruff Python linter and formatter integration.

    Ruff is an extremely fast Python linter and code formatter written in Rust.
    It can replace multiple Python tools like flake8, black, isort, and more.

    Attributes:
        name: str: Tool name.
        description: str: Tool description.
        can_fix: bool: Whether the tool can fix issues.
        config: ToolConfig: Tool configuration.
        exclude_patterns: list[str]: List of patterns to exclude.
        include_venv: bool: Whether to include virtual environment files.
    """

    name: str = "ruff"
    description: str = (
        "Extremely fast Python linter and formatter that replaces multiple tools"
    )
    can_fix: bool = True  # Ruff can both check and fix issues
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=RUFF_DEFAULT_PRIORITY,  # High priority, higher than most linters
            conflicts_with=[],  # Can work alongside other tools
            file_patterns=RUFF_FILE_PATTERNS,  # Python files only
            tool_type=ToolType.LINTER | ToolType.FORMATTER,  # Both linter and formatter
            options={
                "timeout": RUFF_DEFAULT_TIMEOUT,  # Default timeout in seconds
                "select": None,  # Rules to enable
                "ignore": None,  # Rules to ignore
                "extend_select": None,  # Additional rules to enable
                "extend_ignore": None,  # Additional rules to ignore
                "line_length": None,  # Line length limit
                "target_version": None,  # Python version target
                "fix_only": False,  # Only apply fixes, don't report remaining issues
                "unsafe_fixes": False,  # Do NOT enable unsafe fixes by default
                "show_fixes": False,  # Show enumeration of fixes applied
                # Wrapper-first defaults:
                # format_check: include `ruff format --check` during check
                # format: run `ruff format` during fix
                # Default True: `lintro chk` runs formatting and lint checks.
                "format_check": True,
                # Default to running the formatter during fmt to apply
                # reformatting along with lint fixes
                "format": True,
                # Allow disabling the lint-fix stage if users only want
                # formatting changes
                "lint_fix": True,
            },
        ),
    )

    def __post_init__(self) -> None:
        """Initialize the tool with default configuration."""
        super().__post_init__()

        # Load ruff configuration from pyproject.toml
        ruff_config = _load_ruff_config()

        # Load .lintro-ignore patterns
        lintro_ignore_patterns = _load_lintro_ignore()

        # Update exclude patterns from configuration and .lintro-ignore
        if "exclude" in ruff_config:
            self.exclude_patterns.extend(ruff_config["exclude"])
        if lintro_ignore_patterns:
            self.exclude_patterns.extend(lintro_ignore_patterns)

        # Update other options from configuration
        if "line_length" in ruff_config:
            self.options["line_length"] = ruff_config["line_length"]
        if "target_version" in ruff_config:
            self.options["target_version"] = ruff_config["target_version"]
        if "select" in ruff_config:
            self.options["select"] = ruff_config["select"]
        if "ignore" in ruff_config:
            self.options["ignore"] = ruff_config["ignore"]
        if "unsafe_fixes" in ruff_config:
            self.options["unsafe_fixes"] = ruff_config["unsafe_fixes"]

        # Allow environment variable override for unsafe fixes
        # Useful for development and CI environments
        # This must come after config loading to override config values
        env_unsafe_fixes = os.environ.get("RUFF_UNSAFE_FIXES", "").lower()
        if env_unsafe_fixes in ("true", "1", "yes", "on"):
            self.options["unsafe_fixes"] = True

    def set_options(
        self,
        select: list[str] | None = None,
        ignore: list[str] | None = None,
        extend_select: list[str] | None = None,
        extend_ignore: list[str] | None = None,
        line_length: int | None = None,
        target_version: str | None = None,
        fix_only: bool | None = None,
        unsafe_fixes: bool | None = None,
        show_fixes: bool | None = None,
        format: bool | None = None,
        lint_fix: bool | None = None,
        format_check: bool | None = None,
        **kwargs,
    ) -> None:
        """Set Ruff-specific options.

        Args:
            select: list[str] | None: Rules to enable.
            ignore: list[str] | None: Rules to ignore.
            extend_select: list[str] | None: Additional rules to enable.
            extend_ignore: list[str] | None: Additional rules to ignore.
            line_length: int | None: Line length limit.
            target_version: str | None: Python version target.
            fix_only: bool | None: Only apply fixes, don't report remaining issues.
            unsafe_fixes: bool | None: Include unsafe fixes.
            show_fixes: bool | None: Show enumeration of fixes applied.
            format: bool | None: Whether to run `ruff format` during fix.
            lint_fix: bool | None: Whether to run `ruff check --fix` during fix.
            format_check: bool | None: Whether to run `ruff format --check` in check.
            **kwargs: Other tool options.

        Raises:
            ValueError: If an option value is invalid.
        """
        if select is not None:
            if isinstance(select, str):
                select = [select]
            elif not isinstance(select, list):
                raise ValueError("select must be a string or list of rule codes")
        if ignore is not None:
            if isinstance(ignore, str):
                ignore = [ignore]
            elif not isinstance(ignore, list):
                raise ValueError("ignore must be a string or list of rule codes")
        if extend_select is not None:
            if isinstance(extend_select, str):
                extend_select = [extend_select]
            elif not isinstance(extend_select, list):
                raise ValueError("extend_select must be a string or list of rule codes")
        if extend_ignore is not None:
            if isinstance(extend_ignore, str):
                extend_ignore = [extend_ignore]
            elif not isinstance(extend_ignore, list):
                raise ValueError("extend_ignore must be a string or list of rule codes")
        if line_length is not None:
            if not isinstance(line_length, int):
                raise ValueError("line_length must be an integer")
            if line_length <= 0:
                raise ValueError("line_length must be positive")
        if target_version is not None and not isinstance(target_version, str):
            raise ValueError("target_version must be a string")
        if fix_only is not None and not isinstance(fix_only, bool):
            raise ValueError("fix_only must be a boolean")
        if unsafe_fixes is not None and not isinstance(unsafe_fixes, bool):
            raise ValueError("unsafe_fixes must be a boolean")
        if show_fixes is not None and not isinstance(show_fixes, bool):
            raise ValueError("show_fixes must be a boolean")
        if format is not None and not isinstance(format, bool):
            raise ValueError("format must be a boolean")
        if format_check is not None and not isinstance(format_check, bool):
            raise ValueError("format_check must be a boolean")

        options: dict = {
            "select": select,
            "ignore": ignore,
            "extend_select": extend_select,
            "extend_ignore": extend_ignore,
            "line_length": line_length,
            "target_version": target_version,
            "fix_only": fix_only,
            "unsafe_fixes": unsafe_fixes,
            "show_fixes": show_fixes,
            "format": format,
            "lint_fix": lint_fix,
            "format_check": format_check,
        }
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _build_check_command(
        self,
        files: list[str],
        fix: bool = False,
    ) -> list[str]:
        """Build the ruff check command.

        Args:
            files: list[str]: List of files to check.
            fix: bool: Whether to apply fixes.

        Returns:
            list[str]: List of command arguments.
        """
        cmd: list[str] = self._get_executable_command(tool_name="ruff") + ["check"]

        # Add --isolated if in test mode
        if os.environ.get(RUFF_TEST_MODE_ENV) == RUFF_TEST_MODE_VALUE:
            cmd.append("--isolated")

        # Add configuration options
        selected_rules = list(self.options.get("select") or [])
        ignored_rules = set(self.options.get("ignore") or [])
        extend_selected_rules = list(self.options.get("extend_select") or [])

        # Ensure E501 is included when selecting E-family unless explicitly ignored
        if (
            "E" in selected_rules
            and "E501" not in ignored_rules
            and "E501" not in selected_rules
            and "E501" not in extend_selected_rules
        ):
            extend_selected_rules.append("E501")

        if selected_rules:
            cmd.extend(["--select", ",".join(selected_rules)])
        if ignored_rules:
            cmd.extend(["--ignore", ",".join(sorted(ignored_rules))])
        if extend_selected_rules:
            cmd.extend(["--extend-select", ",".join(extend_selected_rules)])
        if self.options.get("extend_ignore"):
            cmd.extend(["--extend-ignore", ",".join(self.options["extend_ignore"])])
        if self.options.get("line_length"):
            cmd.extend(["--line-length", str(self.options["line_length"])])
        if self.options.get("target_version"):
            cmd.extend(["--target-version", self.options["target_version"]])

        # Fix options
        if fix:
            cmd.append("--fix")
            if self.options.get("unsafe_fixes"):
                cmd.append("--unsafe-fixes")
            if self.options.get("show_fixes"):
                cmd.append("--show-fixes")
            if self.options.get("fix_only"):
                cmd.append("--fix-only")

        # Output format
        cmd.extend(["--output-format", RUFF_OUTPUT_FORMAT])

        # Add files
        cmd.extend(files)

        return cmd

    def _build_format_command(
        self,
        files: list[str],
        check_only: bool = False,
    ) -> list[str]:
        """Build the ruff format command.

        Args:
            files: list[str]: List of files to format.
            check_only: bool: Whether to only check formatting without applying changes.

        Returns:
            list[str]: List of command arguments.
        """
        cmd: list[str] = self._get_executable_command(tool_name="ruff") + ["format"]

        if check_only:
            cmd.append("--check")

        # Add configuration options
        if self.options.get("line_length"):
            cmd.extend(["--line-length", str(self.options["line_length"])])
        if self.options.get("target_version"):
            cmd.extend(["--target-version", self.options["target_version"]])

        # Add files
        cmd.extend(files)

        return cmd

    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files with Ruff (lint only by default).

        Args:
            paths: list[str]: List of file or directory paths to check.

        Returns:
            ToolResult: ToolResult instance.
        """
        self._validate_paths(paths=paths)
        if not paths:
            return ToolResult(
                name=self.name,
                success=True,
                output="No files to check.",
                issues_count=0,
            )

        # Use shared utility for file discovery
        python_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )

        if not python_files:
            return ToolResult(
                name=self.name,
                success=True,
                output="No Python files found to check.",
                issues_count=0,
            )

        logger.debug(f"Files to check: {python_files}")

        # Ensure Ruff discovers the correct configuration by setting the
        # working directory to the common parent of the target files and by
        # passing file paths relative to that directory.
        cwd: str | None = self.get_cwd(paths=python_files)
        rel_files: list[str] = [
            os.path.relpath(f, cwd) if cwd else f for f in python_files
        ]

        timeout: int = self.options.get("timeout", RUFF_DEFAULT_TIMEOUT)
        # Lint check
        cmd: list[str] = self._build_check_command(files=rel_files, fix=False)
        success_lint: bool
        output_lint: str
        success_lint, output_lint = self._run_subprocess(
            cmd=cmd,
            timeout=timeout,
            cwd=cwd,
        )
        lint_issues = parse_ruff_output(output=output_lint)
        lint_issues_count: int = len(lint_issues)

        # Optional format check via `format_check` flag
        format_issues_count: int = 0
        format_files: list[str] = []
        format_issues: list[RuffFormatIssue] = []
        if self.options.get("format_check", False):
            format_cmd: list[str] = self._build_format_command(
                files=rel_files,
                check_only=True,
            )
            success_format: bool
            output_format: str
            success_format, output_format = self._run_subprocess(
                cmd=format_cmd,
                timeout=timeout,
                cwd=cwd,
            )
            format_files = parse_ruff_format_check_output(output=output_format)
            # Normalize files to absolute paths to keep behavior consistent with
            # direct CLI calls and stabilize tests that compare exact paths.
            normalized_files: list[str] = []
            for file_path in format_files:
                if cwd and not os.path.isabs(file_path):
                    absolute_path = os.path.abspath(os.path.join(cwd, file_path))
                    normalized_files.append(absolute_path)
                else:
                    normalized_files.append(file_path)
            format_issues_count = len(normalized_files)
            format_issues = [RuffFormatIssue(file=file) for file in normalized_files]

        # Combine results
        issues_count: int = lint_issues_count + format_issues_count
        success: bool = issues_count == 0

        # Suppress narrative blocks; rely on standardized tables and summary lines
        output_summary: str | None = None

        # Combine linting and formatting issues for the formatters
        all_issues = lint_issues + format_issues

        return ToolResult(
            name=self.name,
            success=success,
            output=output_summary,
            issues_count=issues_count,
            issues=all_issues,
        )

    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Fix issues in files with Ruff.

        Args:
            paths: list[str]: List of file or directory paths to fix.

        Returns:
            ToolResult: ToolResult instance.
        """
        self._validate_paths(paths=paths)
        if not paths:
            return ToolResult(
                name=self.name,
                success=True,
                output="No files to fix.",
                issues_count=0,
            )

        # Use shared utility for file discovery
        python_files: list[str] = walk_files_with_excludes(
            paths=paths,
            file_patterns=self.config.file_patterns,
            exclude_patterns=self.exclude_patterns,
            include_venv=self.include_venv,
        )

        if not python_files:
            return ToolResult(
                name=self.name,
                success=True,
                output="No Python files found to fix.",
                issues_count=0,
            )

        logger.debug(f"Files to fix: {python_files}")
        timeout: int = self.options.get("timeout", RUFF_DEFAULT_TIMEOUT)
        all_outputs: list[str] = []
        overall_success: bool = True

        # Track unsafe fixes for internal decisioning; do not emit as user-facing noise
        unsafe_fixes_enabled: bool = self.options.get("unsafe_fixes", False)

        # First, count issues before fixing
        cmd_check: list[str] = self._build_check_command(files=python_files, fix=False)
        success_check: bool
        output_check: str
        success_check, output_check = self._run_subprocess(
            cmd=cmd_check,
            timeout=timeout,
        )
        initial_issues = parse_ruff_output(output=output_check)
        initial_count: int = len(initial_issues)

        # Also check formatting issues before fixing
        initial_format_count: int = 0
        format_files: list[str] = []
        if self.options.get("format", False):
            format_cmd_check: list[str] = self._build_format_command(
                files=python_files,
                check_only=True,
            )
            success_format_check: bool
            output_format_check: str
            success_format_check, output_format_check = self._run_subprocess(
                cmd=format_cmd_check,
                timeout=timeout,
            )
            format_files = parse_ruff_format_check_output(output=output_format_check)
            initial_format_count = len(format_files)

        # Track initial totals separately for accurate fixed/remaining math
        total_initial_count: int = initial_count + initial_format_count

        # Optionally run ruff check --fix (lint fixes)
        remaining_issues = []
        remaining_count = 0
        success: bool = True  # Default to True when lint_fix is disabled
        if self.options.get("lint_fix", True):
            cmd: list[str] = self._build_check_command(files=python_files, fix=True)
            output: str
            success, output = self._run_subprocess(cmd=cmd, timeout=timeout)
            remaining_issues = parse_ruff_output(output=output)
            remaining_count = len(remaining_issues)

        # Compute fixed lint issues by diffing initial vs remaining (internal only)
        # Not used for display; summary counts reflect totals.

        # Calculate how many lint issues were actually fixed
        fixed_lint_count: int = max(0, initial_count - remaining_count)
        fixed_count: int = fixed_lint_count

        # Do not print raw initial counts; keep output concise and unified

        # Do not print intermediate fixed counts; unify after formatting phase

        # If there are remaining issues, check if any are fixable with unsafe fixes
        if remaining_count > 0:
            # If unsafe fixes are disabled, check if any remaining issues are
            # fixable with unsafe fixes
            if not unsafe_fixes_enabled:
                # Try running ruff with unsafe fixes in dry-run mode to see if it
                # would fix more
                cmd_unsafe: list[str] = self._build_check_command(
                    files=python_files,
                    fix=True,
                )
                if "--unsafe-fixes" not in cmd_unsafe:
                    cmd_unsafe.append("--unsafe-fixes")
                # Only run if not already run with unsafe fixes
                success_unsafe: bool
                output_unsafe: str
                success_unsafe, output_unsafe = self._run_subprocess(
                    cmd=cmd_unsafe,
                    timeout=timeout,
                )
                remaining_unsafe = parse_ruff_output(output=output_unsafe)
                if len(remaining_unsafe) < remaining_count:
                    all_outputs.append(
                        "Some remaining issues could be fixed by enabling unsafe "
                        "fixes (use --tool-options ruff:unsafe_fixes=True)",
                    )
            all_outputs.append(
                f"{remaining_count} issue(s) cannot be auto-fixed",
            )
            for issue in remaining_issues[:DEFAULT_REMAINING_ISSUES_DISPLAY]:
                file_path: str = getattr(issue, "file", "")
                try:
                    file_rel: str = os.path.relpath(file_path)
                except (ValueError, TypeError):
                    file_rel = file_path
                all_outputs.append(
                    f"  {file_rel}:{getattr(issue, 'line', '?')} - "
                    f"{getattr(issue, 'message', 'Unknown issue')}",
                )
            if len(remaining_issues) > DEFAULT_REMAINING_ISSUES_DISPLAY:
                all_outputs.append(
                    f"  ... and "
                    f"{len(remaining_issues) - DEFAULT_REMAINING_ISSUES_DISPLAY} more",
                )

        if total_initial_count == 0:
            # Avoid duplicate success messages; rely on unified logger
            pass
        elif remaining_count == 0 and fixed_count > 0:
            all_outputs.append("All linting issues were successfully auto-fixed")

        if not (success and remaining_count == 0):
            overall_success = False

        # Run ruff format if enabled (default: True)
        if self.options.get("format", False):
            format_cmd: list[str] = self._build_format_command(
                files=python_files,
                check_only=False,
            )
            format_success: bool
            format_output: str
            format_success, format_output = self._run_subprocess(
                cmd=format_cmd,
                timeout=timeout,
            )
            # Formatting fixes are counted separately from lint fixes
            if initial_format_count > 0:
                fixed_count = fixed_lint_count + initial_format_count
            # Suppress raw formatter output for consistency; rely on unified summary
            # Only consider formatting failure if there are actual formatting
            # issues. Don't fail the overall operation just because formatting
            # failed when there are no issues
            if not format_success and total_initial_count > 0:
                overall_success = False

        # Build concise, unified summary output for fmt runs
        summary_lines: list[str] = []
        if fixed_count > 0:
            summary_lines.append(f"Fixed {fixed_count} issue(s)")
        if remaining_count > 0:
            summary_lines.append(
                f"Found {remaining_count} issue(s) that cannot be auto-fixed",
            )
        final_output: str = (
            "\n".join(summary_lines) if summary_lines else "No fixes applied."
        )

        # Success should be based on whether there are remaining issues after fixing
        # If there are no initial issues, success should be True
        overall_success = True if total_initial_count == 0 else remaining_count == 0

        return ToolResult(
            name=self.name,
            success=overall_success,
            output=final_output,
            # For fix operations, issues_count represents remaining for summaries
            issues_count=remaining_count,
            # Display remaining issues only to align tables with summary counts
            issues=remaining_issues,
            initial_issues_count=total_initial_count,
            fixed_issues_count=fixed_count,
            remaining_issues_count=remaining_count,
        )
