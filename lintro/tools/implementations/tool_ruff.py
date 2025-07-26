"""Ruff Python linter and formatter integration."""

from dataclasses import dataclass, field
from typing import Any

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


@dataclass
class RuffTool(BaseTool):
    """Ruff Python linter and formatter integration.

    Ruff is an extremely fast Python linter and code formatter written in Rust.
    It can replace multiple Python tools like flake8, black, isort, and more.

    Attributes:
        name: Tool name
        description: Tool description
        can_fix: Whether the tool can fix issues
        config: Tool configuration
        exclude_patterns: List of patterns to exclude
        include_venv: Whether to include virtual environment files
    """

    name: str = "ruff"
    description: str = (
        "Extremely fast Python linter and formatter that replaces multiple tools"
    )
    can_fix: bool = True  # Ruff can both check and fix issues
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=85,  # High priority, higher than most linters
            conflicts_with=[],  # Can work alongside other tools
            file_patterns=["*.py", "*.pyi"],  # Python files only
            tool_type=ToolType.LINTER | ToolType.FORMATTER,  # Both linter and formatter
            options={
                "timeout": 30,  # Default timeout in seconds
                "select": None,  # Rules to enable
                "ignore": None,  # Rules to ignore
                "extend_select": None,  # Additional rules to enable
                "extend_ignore": None,  # Additional rules to ignore
                "line_length": None,  # Line length limit
                "target_version": None,  # Python version target
                "fix_only": False,  # Only apply fixes, don't report remaining issues
                "unsafe_fixes": False,  # Do NOT enable unsafe fixes by default
                "show_fixes": False,  # Show enumeration of fixes applied
                "format": True,  # Whether to run formatter as well
            },
        ),
    )

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
        **kwargs: Any,
    ) -> None:
        """Set Ruff-specific options.

        Args:
            select: Rules to enable
            ignore: Rules to ignore
            extend_select: Additional rules to enable
            extend_ignore: Additional rules to ignore
            line_length: Line length limit
            target_version: Python version target
            fix_only: Only apply fixes, don't report remaining issues
            unsafe_fixes: Include unsafe fixes
            show_fixes: Show enumeration of fixes applied
            format: Whether to run formatter as well
            **kwargs: Other tool options

        Raises:
            ValueError: If an option value is invalid
        """
        if select is not None and not isinstance(select, list):
            raise ValueError("select must be a list of rule codes")
        if ignore is not None and not isinstance(ignore, list):
            raise ValueError("ignore must be a list of rule codes")
        if extend_select is not None and not isinstance(extend_select, list):
            raise ValueError("extend_select must be a list of rule codes")
        if extend_ignore is not None and not isinstance(extend_ignore, list):
            raise ValueError("extend_ignore must be a list of rule codes")
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

        options = {
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
            files: List of files to check
            fix: Whether to apply fixes

        Returns:
            List of command arguments
        """
        import os

        cmd = self._get_executable_command("ruff") + ["check"]

        # Add --isolated if in test mode
        if os.environ.get("LINTRO_TEST_MODE") == "1":
            cmd.append("--isolated")

        # Add configuration options
        if self.options.get("select"):
            cmd.extend(["--select", ",".join(self.options["select"])])
        if self.options.get("ignore"):
            cmd.extend(["--ignore", ",".join(self.options["ignore"])])
        if self.options.get("extend_select"):
            cmd.extend(["--extend-select", ",".join(self.options["extend_select"])])
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
        cmd.extend(["--output-format", "json"])

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
            files: List of files to format
            check_only: Whether to only check formatting without applying changes

        Returns:
            List of command arguments
        """
        cmd = self._get_executable_command("ruff") + ["format"]

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
        """Check files with Ruff (lint and format).

        Args:
            paths: List of file or directory paths to check

        Returns:
            ToolResult instance
        """
        self._validate_paths(paths)
        if not paths:
            return ToolResult(
                name=self.name,
                success=True,
                output="No files to check.",
                issues_count=0,
            )

        # Use shared utility for file discovery
        python_files = walk_files_with_excludes(
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

        timeout = self.options.get("timeout", 30)
        # Lint check
        cmd = self._build_check_command(python_files, fix=False)
        success_lint, output_lint = self._run_subprocess(cmd, timeout=timeout)
        lint_issues = parse_ruff_output(output_lint)
        lint_issues_count = len(lint_issues)

        # Format check (only if format option is enabled)
        format_issues_count = 0
        format_files = []
        format_issues = []
        if self.options.get("format", True):
            format_cmd = self._build_format_command(python_files, check_only=True)
            success_format, output_format = self._run_subprocess(
                format_cmd, timeout=timeout
            )
            format_files = parse_ruff_format_check_output(output_format)
            format_issues_count = len(format_files)
            # Create RuffFormatIssue objects for each file that would be reformatted
            format_issues = [RuffFormatIssue(file=file) for file in format_files]

        # Combine results
        issues_count = lint_issues_count + format_issues_count
        success = issues_count == 0

        # Format output for display (matching ruff's native output format)
        output_lines = []

        # Add linting issues (matching ruff's format)
        if lint_issues_count > 0:
            for issue in lint_issues:
                output_lines.append(
                    f"{issue.file}:{issue.line}:{issue.column}: "
                    f"{issue.code} {issue.message}"
                )

            # Calculate fixable count from linting issues
            fixable_count = sum(1 for issue in lint_issues if issue.fixable)
            output_lines.append(f"Found {lint_issues_count} errors.")
            if fixable_count > 0:
                output_lines.append(
                    f"[*] {fixable_count} fixable with the --fix option."
                )

        # Add formatting issues (matching ruff's format)
        if format_issues_count > 0 and self.options.get("format", True):
            for file in format_files:
                output_lines.append(f"Would reformat: {file}")
            output_lines.append(
                f"{format_issues_count} file{'s' if format_issues_count > 1 else ''} "
                "would be reformatted"
            )

        if not output_lines:
            output_lines.append("No issues found.")

        output_summary = "\n".join(output_lines)

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
            paths: List of file or directory paths to fix

        Returns:
            ToolResult instance
        """
        self._validate_paths(paths)
        if not paths:
            return ToolResult(
                name=self.name,
                success=True,
                output="No files to fix.",
                issues_count=0,
            )

        # Use shared utility for file discovery
        python_files = walk_files_with_excludes(
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
        timeout = self.options.get("timeout", 30)
        all_outputs = []
        overall_success = True

        # Show unsafe fixes status
        unsafe_fixes_enabled = self.options.get("unsafe_fixes", False)
        if unsafe_fixes_enabled:
            logger.info(
                "[ruff] Unsafe fixes are ENABLED (may apply aggressive changes)"
            )
        else:
            logger.info(
                "[ruff] Unsafe fixes are DISABLED (some issues may not be auto-fixable)"
            )

        # First, count issues before fixing
        cmd_check = self._build_check_command(python_files, fix=False)
        success_check, output_check = self._run_subprocess(cmd_check, timeout=timeout)
        initial_issues = parse_ruff_output(output_check)
        initial_count = len(initial_issues)

        # Also check formatting issues before fixing
        format_cmd_check = self._build_format_command(python_files, check_only=True)
        success_format_check, output_format_check = self._run_subprocess(
            format_cmd_check, timeout=timeout
        )
        format_files = parse_ruff_format_check_output(output_format_check)
        initial_format_count = len(format_files)

        # Total initial issues (linting + formatting)
        total_initial_count = initial_count + initial_format_count

        # Run ruff check --fix to apply fixes
        cmd = self._build_check_command(python_files, fix=True)
        success, output = self._run_subprocess(cmd, timeout=timeout)
        remaining_issues = parse_ruff_output(output)
        remaining_count = len(remaining_issues)

        # Calculate how many issues were actually fixed
        fixed_count = total_initial_count - remaining_count

        # Show initial count and fixable count (matching ruff's native output format)
        if initial_count > 0:
            # Calculate fixable count from initial issues
            fixable_count = sum(1 for issue in initial_issues if issue.fixable)
            all_outputs.append(f"Found {initial_count} errors.")
            if fixable_count > 0:
                all_outputs.append(
                    f"[*] {fixable_count} fixable with the --fix option."
                )

        if fixed_count > 0:
            all_outputs.append(f"Fixed {fixed_count} issue(s)")

        # If there are remaining issues, check if any are fixable with unsafe fixes
        if remaining_count > 0:
            # If unsafe fixes are disabled, check if any remaining issues are
            # fixable with unsafe fixes
            if not unsafe_fixes_enabled:
                # Try running ruff with unsafe fixes in dry-run mode to see if it
                # would fix more
                cmd_unsafe = self._build_check_command(python_files, fix=True)
                if "--unsafe-fixes" not in cmd_unsafe:
                    cmd_unsafe.append("--unsafe-fixes")
                # Only run if not already run with unsafe fixes
                success_unsafe, output_unsafe = self._run_subprocess(
                    cmd_unsafe, timeout=timeout
                )
                remaining_unsafe = parse_ruff_output(output_unsafe)
                if len(remaining_unsafe) < remaining_count:
                    all_outputs.append(
                        "Some remaining issues could be fixed by enabling unsafe "
                        "fixes (use --tool-options ruff:unsafe_fixes=True)"
                    )
            all_outputs.append(
                f"Found {remaining_count} issue(s) that cannot be auto-fixed"
            )
            for issue in remaining_issues[:5]:
                file_path = getattr(issue, "file", "")
                import os

                try:
                    file_rel = os.path.relpath(file_path)
                except (ValueError, TypeError):
                    file_rel = file_path
                all_outputs.append(
                    f"  {file_rel}:{getattr(issue, 'line', '?')} - "
                    f"{getattr(issue, 'message', 'Unknown issue')}"
                )
            if len(remaining_issues) > 5:
                all_outputs.append(f"  ... and {len(remaining_issues) - 5} more")

        if total_initial_count == 0:
            all_outputs.append("No linting issues found")
        elif remaining_count == 0 and fixed_count > 0:
            all_outputs.append("All linting issues were successfully auto-fixed")

        if not (success and remaining_count == 0):
            overall_success = False

        # Run ruff format if enabled
        if self.options.get("format", True):
            format_cmd = self._build_format_command(python_files, check_only=False)
            format_success, format_output = self._run_subprocess(
                format_cmd, timeout=timeout
            )
            if format_output and format_output.strip():
                all_outputs.append(f"Formatting:\n{format_output}")
            else:
                all_outputs.append("No formatting changes needed")
            # Only consider formatting failure if there are actual formatting
            # issues. Don't fail the overall operation just because formatting
            # failed when there are no issues
            if not format_success and total_initial_count > 0:
                overall_success = False

        final_output = "\n\n".join(all_outputs) if all_outputs else "No fixes applied."

        # Success should be based on whether there are remaining issues after fixing
        # If there are no initial issues, success should be True
        if total_initial_count == 0:
            overall_success = True
        else:
            overall_success = remaining_count == 0

        return ToolResult(
            name=self.name,
            success=overall_success,
            output=final_output,
            issues_count=fixed_count,
            issues=remaining_issues,  # Include remaining issues for grid formatting
        )
