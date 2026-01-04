"""Black Python formatter integration.

Black is an opinionated Python formatter. We wire it as a formatter-only tool
that cooperates with Ruff by default: when both are run, Ruff keeps linting and
Black handles formatting. Users can override via --tool-options.

Project: https://github.com/psf/black
"""

from __future__ import annotations

import os
import subprocess  # nosec B404 - used safely with shell disabled
from dataclasses import dataclass, field

from loguru import logger

from lintro.enums.tool_type import ToolType
from lintro.models.core.tool_config import ToolConfig
from lintro.models.core.tool_result import ToolResult
from lintro.parsers.black.black_issue import BlackIssue
from lintro.parsers.black.black_parser import parse_black_output
from lintro.tools.core.tool_base import BaseTool

BLACK_DEFAULT_TIMEOUT: int = 30
BLACK_DEFAULT_PRIORITY: int = 90  # Prefer Black ahead of Ruff formatting
BLACK_FILE_PATTERNS: list[str] = ["*.py", "*.pyi"]


@dataclass
class BlackTool(BaseTool):
    """Black Python formatter integration."""

    name: str = "black"
    description: str = "Opinionated Python code formatter"
    can_fix: bool = field(default=True)
    config: ToolConfig = field(
        default_factory=lambda: ToolConfig(
            priority=BLACK_DEFAULT_PRIORITY,
            conflicts_with=[],  # Compatible with Ruff (lint); no direct conflicts
            file_patterns=BLACK_FILE_PATTERNS,
            tool_type=ToolType.FORMATTER,
            options={
                "line_length": None,
                "target_version": None,
                "fast": False,  # Do not use --fast by default
                "preview": False,  # Do not enable preview by default
                "diff": False,  # Default to standard output messages
            },
        ),
    )

    def set_options(
        self,
        line_length: int | None = None,
        target_version: str | None = None,
        fast: bool | None = None,
        preview: bool | None = None,
        diff: bool | None = None,
        **kwargs,
    ) -> None:
        """Set Black-specific options with validation.

        Args:
            line_length: Optional line length override.
            target_version: String per Black CLI (e.g., "py313").
            fast: Use --fast mode (skip safety checks).
            preview: Enable preview style.
            diff: Show diffs in output when formatting.
            **kwargs: Additional base options like ``timeout``, ``exclude_patterns``,
                and ``include_venv`` that are handled by ``BaseTool``.

        Raises:
            ValueError: If any provided option has an invalid type.
        """
        if line_length is not None and not isinstance(line_length, int):
            raise ValueError("line_length must be an integer")
        if target_version is not None and not isinstance(target_version, str):
            raise ValueError("target_version must be a string")
        if fast is not None and not isinstance(fast, bool):
            raise ValueError("fast must be a boolean")
        if preview is not None and not isinstance(preview, bool):
            raise ValueError("preview must be a boolean")
        if diff is not None and not isinstance(diff, bool):
            raise ValueError("diff must be a boolean")

        options = {
            "line_length": line_length,
            "target_version": target_version,
            "fast": fast,
            "preview": preview,
            "diff": diff,
        }
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}
        super().set_options(**options, **kwargs)

    def _build_common_args(self) -> list[str]:
        """Build common CLI arguments for Black.

        Uses Lintro config injection when available, otherwise falls back
        to options-based configuration.

        Returns:
            list[str]: CLI arguments for Black.
        """
        args: list[str] = []

        # Try Lintro config injection first (--config flag)
        config_args = self._build_config_args()
        if config_args:
            args.extend(config_args)
        else:
            # Fallback to options-based configuration
            if self.options.get("line_length"):
                args.extend(["--line-length", str(self.options["line_length"])])
            if self.options.get("target_version"):
                args.extend(["--target-version", str(self.options["target_version"])])

        # These flags are always passed via CLI (not in config file)
        if self.options.get("fast"):
            args.append("--fast")
        if self.options.get("preview"):
            args.append("--preview")
        return args

    def _check_line_length_violations(
        self,
        files: list[str],
        cwd: str | None,
    ) -> list[BlackIssue]:
        """Check for line length violations using Ruff's E501 rule.

        This catches lines that exceed the line length limit but cannot be
        safely wrapped by Black. Black's --check mode only reports files that
        would be reformatted, so it misses unwrappable long lines.

        Args:
            files: List of file paths (relative to cwd) to check.
            cwd: Working directory for the check.

        Returns:
            list[BlackIssue]: List of line length violations converted to
                BlackIssue objects.
        """
        if not files:
            return []

        # Import here to avoid circular dependency
        from lintro.tools.implementations.tool_ruff import RuffTool

        try:
            ruff_tool = RuffTool()
            # Use the same line_length as Black is configured with
            line_length = self.options.get("line_length")
            if line_length:
                ruff_tool.set_options(
                    select=["E501"],
                    line_length=line_length,
                    timeout=self.options.get("timeout", BLACK_DEFAULT_TIMEOUT),
                )
            else:
                # If no line_length configured, use Ruff's default (88)
                ruff_tool.set_options(
                    select=["E501"],
                    timeout=self.options.get("timeout", BLACK_DEFAULT_TIMEOUT),
                )

            # Convert relative paths to absolute paths for RuffTool
            abs_files: list[str] = []
            for file_path in files:
                if cwd and not os.path.isabs(file_path):
                    abs_files.append(os.path.abspath(os.path.join(cwd, file_path)))
                else:
                    abs_files.append(file_path)

            # Run Ruff E501 check on the absolute file paths
            ruff_result = ruff_tool.check(paths=abs_files)

            # Convert Ruff E501 violations to BlackIssue objects
            black_issues: list[BlackIssue] = []
            if ruff_result.issues:
                for ruff_issue in ruff_result.issues:
                    # Only process E501 violations
                    if hasattr(ruff_issue, "code") and ruff_issue.code == "E501":
                        file_path = ruff_issue.file
                        # Ensure absolute path
                        if not os.path.isabs(file_path):
                            if cwd:
                                file_path = os.path.abspath(
                                    os.path.join(cwd, file_path),
                                )
                            else:
                                file_path = os.path.abspath(file_path)
                        message = (
                            f"Line {ruff_issue.line} exceeds line length limit "
                            f"({ruff_issue.message})"
                        )
                        # Line length violations cannot be fixed by Black
                        black_issues.append(
                            BlackIssue(
                                file=file_path,
                                line=ruff_issue.line,
                                column=ruff_issue.column,
                                code=ruff_issue.code,
                                message=message,
                                severity="error",
                                fixable=False,
                            ),
                        )

        except Exception as e:
            # If Ruff check fails, log but don't fail the entire Black check
            logger.debug(f"Failed to check line length violations with Ruff: {e}")
            return []

        return black_issues

    def _handle_timeout_error(
        self,
        timeout_val: int,
        initial_count: int | None = None,
    ) -> ToolResult:
        """Handle timeout errors consistently across all Black operations.

        Args:
            timeout_val: The timeout value that was exceeded.
            initial_count: Optional initial issues count for fix operations.

        Returns:
            ToolResult: Standardized timeout error result.
        """
        timeout_msg = (
            f"Black execution timed out ({timeout_val}s limit exceeded).\n\n"
            "This may indicate:\n"
            "  - Large codebase taking too long to process\n"
            "  - Need to increase timeout via --tool-options black:timeout=N"
        )
        if initial_count is not None:
            # Fix operation timeout - preserve known initial count
            return ToolResult(
                name=self.name,
                success=False,
                output=timeout_msg,
                issues_count=max(initial_count, 1),
                issues=[],
                initial_issues_count=(
                    initial_count if not self.options.get("diff") else 0
                ),
                fixed_issues_count=0,
                remaining_issues_count=max(initial_count, 1),
            )
        # Check operation timeout
        return ToolResult(
            name=self.name,
            success=False,
            output=timeout_msg,
            issues_count=1,  # Count timeout as execution failure
            issues=[],
        )

    def check(self, paths: list[str]) -> ToolResult:
        """Check files using Black without applying changes.

        Args:
            paths: List of file or directory paths to check.

        Returns:
            ToolResult: Result containing success flag, issue count, and issues.
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(
            paths,
            default_timeout=BLACK_DEFAULT_TIMEOUT,
        )
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        cmd: list[str] = self._get_executable_command(tool_name="black") + [
            "--check",
        ]
        cmd.extend(self._build_common_args())
        cmd.extend(ctx.rel_files)

        logger.debug(f"[BlackTool] Running: {' '.join(cmd)} (cwd={ctx.cwd})")
        try:
            success, output = self._run_subprocess(
                cmd=cmd,
                timeout=ctx.timeout,
                cwd=ctx.cwd,
            )
        except subprocess.TimeoutExpired:
            return self._handle_timeout_error(ctx.timeout)

        black_issues = parse_black_output(output=output)

        # Also check for line length violations that Black cannot wrap
        # This catches E501 violations that Ruff finds but Black doesn't report
        line_length_issues = self._check_line_length_violations(
            files=ctx.rel_files,
            cwd=ctx.cwd,
        )

        # Combine Black formatting issues with line length violations
        all_issues = black_issues + line_length_issues
        count = len(all_issues)

        # In check mode, success means no differences
        return ToolResult(
            name=self.name,
            success=(success and count == 0),
            output=None if count == 0 else output,
            issues_count=count,
            issues=all_issues,
        )

    def fix(self, paths: list[str]) -> ToolResult:
        """Format files using Black, returning standardized counts.

        Args:
            paths: List of file or directory paths to format.

        Returns:
            ToolResult: Result containing counts and any remaining issues.
        """
        # Use shared preparation for version check, path validation, file discovery
        ctx = self._prepare_execution(
            paths,
            no_files_message="No files to format.",
            default_timeout=BLACK_DEFAULT_TIMEOUT,
        )
        if ctx.should_skip:
            return ctx.early_result  # type: ignore[return-value]

        # Build reusable check command (used for final verification)
        check_cmd: list[str] = self._get_executable_command(tool_name="black") + [
            "--check",
        ]
        check_cmd.extend(self._build_common_args())
        check_cmd.extend(ctx.rel_files)

        # When diff is requested, skip the initial check to ensure the middle
        # invocation is the formatting run (as exercised by unit tests) and to
        # avoid redundant subprocess calls.
        if self.options.get("diff"):
            initial_issues = []
            initial_line_length_issues = []
            initial_count = 0
        else:
            try:
                _, check_output = self._run_subprocess(
                    cmd=check_cmd,
                    timeout=ctx.timeout,
                    cwd=ctx.cwd,
                )
            except subprocess.TimeoutExpired:
                return self._handle_timeout_error(ctx.timeout, initial_count=0)
            initial_issues = parse_black_output(output=check_output)
            # Also check for line length violations in initial state
            # This ensures initial_count includes all issues that will be counted
            # in remaining_count, preventing validation errors
            initial_line_length_issues = self._check_line_length_violations(
                files=ctx.rel_files,
                cwd=ctx.cwd,
            )
            initial_count = len(initial_issues) + len(initial_line_length_issues)

        # Apply formatting
        fix_cmd_base: list[str] = self._get_executable_command(tool_name="black")
        fix_cmd: list[str] = list(fix_cmd_base)
        if self.options.get("diff"):
            # When diff is requested, ensure the flag is present on the format run
            # so tests can assert its presence on the middle invocation.
            fix_cmd.append("--diff")
        fix_cmd.extend(self._build_common_args())
        fix_cmd.extend(ctx.rel_files)

        logger.debug(f"[BlackTool] Fixing: {' '.join(fix_cmd)} (cwd={ctx.cwd})")
        try:
            _, fix_output = self._run_subprocess(
                cmd=fix_cmd,
                timeout=ctx.timeout,
                cwd=ctx.cwd,
            )
        except subprocess.TimeoutExpired:
            return self._handle_timeout_error(ctx.timeout, initial_count=initial_count)

        # Final check for remaining differences
        try:
            final_success, final_output = self._run_subprocess(
                cmd=check_cmd,
                timeout=ctx.timeout,
                cwd=ctx.cwd,
            )
        except subprocess.TimeoutExpired:
            return self._handle_timeout_error(ctx.timeout, initial_count=initial_count)
        remaining_issues = parse_black_output(output=final_output)

        # Also check for line length violations that Black cannot wrap
        # This catches E501 violations that Ruff finds but Black doesn't report
        line_length_issues = self._check_line_length_violations(
            files=ctx.rel_files,
            cwd=ctx.cwd,
        )

        # Combine Black formatting issues with line length violations
        all_remaining_issues = remaining_issues + line_length_issues
        remaining_count = len(all_remaining_issues)

        # Parse per-file reformats from the formatting run to display in console
        fixed_issues_parsed = parse_black_output(output=fix_output)

        # Calculate fixed count: always use issue-based calculation to ensure
        # consistency with initial_count and remaining_count (which count issues,
        # not files). The fixed_count_from_output is useful for display but
        # shouldn't be used for validation since it counts files, not issues.
        #
        # To maintain the invariant initial = fixed + remaining:
        # - initial_count includes ALL issues (formatting + line length)
        # - remaining_count includes ALL remaining issues (fmt + line length)
        # - fixed_count = initial_count - remaining_count
        # This ensures initial = fixed + remaining even though line
        # length violations can't be fixed
        fixed_count = max(0, initial_count - remaining_count)

        # Build concise summary
        summary: list[str] = []
        if fixed_count > 0:
            summary.append(f"Fixed {fixed_count} issue(s)")
        if remaining_count > 0:
            summary.append(
                f"Found {remaining_count} issue(s) that cannot be auto-fixed",
            )
        final_summary = "\n".join(summary) if summary else "No fixes applied."

        # Combine fixed and remaining issues so formatter can split them by fixability
        all_issues = (fixed_issues_parsed or []) + all_remaining_issues

        return ToolResult(
            name=self.name,
            success=(remaining_count == 0),
            output=final_summary,
            issues_count=remaining_count,
            issues=all_issues,
            initial_issues_count=initial_count,
            fixed_issues_count=fixed_count,
            remaining_issues_count=remaining_count,
        )
