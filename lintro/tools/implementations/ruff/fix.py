"""Ruff fix execution logic.

Functions for running ruff fix commands and processing results.
"""

import os
import subprocess  # nosec B404 - subprocess used safely to execute ruff commands with controlled input
from typing import TYPE_CHECKING

from lintro.parsers.ruff.ruff_issue import RuffFormatIssue
from lintro.parsers.ruff.ruff_parser import (
    parse_ruff_format_check_output,
    parse_ruff_output,
)
from lintro.tools.core.timeout_utils import (
    create_timeout_result,
    get_timeout_value,
)
from lintro.utils.path_filtering import walk_files_with_excludes

if TYPE_CHECKING:
    from lintro.models.core.tool_result import ToolResult
    from lintro.tools.implementations.tool_ruff import RuffTool

# Constants from tool_ruff.py
RUFF_DEFAULT_TIMEOUT: int = 30
DEFAULT_REMAINING_ISSUES_DISPLAY: int = 5


def execute_ruff_fix(
    tool: "RuffTool",
    paths: list[str],
) -> "ToolResult":
    """Execute ruff fix command and process results.

    Args:
        tool: RuffTool instance
        paths: list[str]: List of file or directory paths to fix.

    Returns:
        ToolResult: ToolResult instance.
    """
    from lintro.models.core.tool_result import ToolResult
    from lintro.tools.implementations.ruff.commands import (
        build_ruff_check_command,
        build_ruff_format_command,
    )

    # Check version requirements
    version_result = tool._verify_tool_version()
    if version_result is not None:
        return version_result

    tool._validate_paths(paths=paths)
    if not paths:
        return ToolResult(
            name=tool.name,
            success=True,
            output="No files to fix.",
            issues_count=0,
        )

    # Use shared utility for file discovery
    python_files: list[str] = walk_files_with_excludes(
        paths=paths,
        file_patterns=tool.config.file_patterns,
        exclude_patterns=tool.exclude_patterns,
        include_venv=tool.include_venv,
    )

    if not python_files:
        return ToolResult(
            name=tool.name,
            success=True,
            output="No Python files found to fix.",
            issues_count=0,
        )

    timeout: int = get_timeout_value(tool, RUFF_DEFAULT_TIMEOUT)
    all_outputs: list[str] = []
    overall_success: bool = True

    # Track unsafe fixes for internal decisioning; do not emit as user-facing noise
    unsafe_fixes_enabled: bool = tool.options.get("unsafe_fixes", False)

    # First, count issues before fixing
    cmd_check: list[str] = build_ruff_check_command(
        tool=tool,
        files=python_files,
        fix=False,
    )
    success_check: bool
    output_check: str
    try:
        success_check, output_check = tool._run_subprocess(
            cmd=cmd_check,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        timeout_result = create_timeout_result(
            tool=tool,
            timeout=timeout,
            cmd=cmd_check,
        )
        return ToolResult(
            name=tool.name,
            success=timeout_result["success"],
            output=timeout_result["output"],
            issues_count=timeout_result["issues_count"],
            issues=timeout_result["issues"],
            initial_issues_count=0,
            fixed_issues_count=0,
            remaining_issues_count=1,
        )
    initial_issues = parse_ruff_output(output=output_check)
    initial_count: int = len(initial_issues)

    # Also check formatting issues before fixing
    initial_format_count: int = 0
    format_files: list[str] = []
    if tool.options.get("format", False):
        format_cmd_check: list[str] = build_ruff_format_command(
            tool=tool,
            files=python_files,
            check_only=True,
        )
        success_format_check: bool
        output_format_check: str
        try:
            success_format_check, output_format_check = tool._run_subprocess(
                cmd=format_cmd_check,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            timeout_msg = (
                f"Ruff execution timed out ({timeout}s limit exceeded).\n\n"
                "This may indicate:\n"
                "  - Large codebase taking too long to process\n"
                "  - Need to increase timeout via --tool-options ruff:timeout=N"
            )
            return ToolResult(
                name=tool.name,
                success=False,
                output=timeout_msg,
                issues_count=1,  # Count timeout as execution failure
                # Include any lint issues found before timeout
                issues=initial_issues,
                initial_issues_count=initial_count,
                fixed_issues_count=0,
                remaining_issues_count=1,
            )
        format_files = parse_ruff_format_check_output(output=output_format_check)
        initial_format_count = len(format_files)

    # Track initial totals separately for accurate fixed/remaining math
    total_initial_count: int = initial_count + initial_format_count

    # Optionally run ruff check --fix (lint fixes)
    remaining_issues = []
    remaining_count = 0
    success: bool = True  # Default to True when lint_fix is disabled
    if tool.options.get("lint_fix", True):
        cmd: list[str] = build_ruff_check_command(
            tool=tool,
            files=python_files,
            fix=True,
        )
        output: str
        try:
            success, output = tool._run_subprocess(cmd=cmd, timeout=timeout)
        except subprocess.TimeoutExpired:
            timeout_msg = (
                f"Ruff execution timed out ({timeout}s limit exceeded).\n\n"
                "This may indicate:\n"
                "  - Large codebase taking too long to process\n"
                "  - Need to increase timeout via --tool-options ruff:timeout=N"
            )
            return ToolResult(
                name=tool.name,
                success=False,
                output=timeout_msg,
                issues_count=1,  # Count timeout as execution failure
                issues=initial_issues,  # Include initial issues found
                initial_issues_count=total_initial_count,
                fixed_issues_count=0,
                remaining_issues_count=1,
            )
        remaining_issues = parse_ruff_output(output=output)
        remaining_count = len(remaining_issues)

    # Compute fixed lint issues by diffing initial vs remaining (internal only)
    # Not used for display; summary counts reflect totals.

    # Calculate how many lint issues were actually fixed
    fixed_lint_count: int = max(0, initial_count - remaining_count)
    fixed_count: int = fixed_lint_count

    # If there are remaining issues, check if any are fixable with unsafe fixes
    if remaining_count > 0:
        # If unsafe fixes are disabled, check if any remaining issues are
        # fixable with unsafe fixes
        if not unsafe_fixes_enabled:
            # Try running ruff with unsafe fixes in dry-run mode to see if it
            # would fix more
            cmd_unsafe: list[str] = build_ruff_check_command(
                tool=tool,
                files=python_files,
                fix=True,
            )
            if "--unsafe-fixes" not in cmd_unsafe:
                cmd_unsafe.append("--unsafe-fixes")
            # Only run if not already run with unsafe fixes
            success_unsafe: bool
            output_unsafe: str
            try:
                success_unsafe, output_unsafe = tool._run_subprocess(
                    cmd=cmd_unsafe,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                # If unsafe check times out, just continue with current results
                # Don't fail the entire operation for this optional check
                remaining_unsafe = remaining_issues
            else:
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
    if tool.options.get("format", False):
        format_cmd: list[str] = build_ruff_format_command(
            tool=tool,
            files=python_files,
            check_only=False,
        )
        format_success: bool
        format_output: str
        try:
            format_success, format_output = tool._run_subprocess(
                cmd=format_cmd,
                timeout=timeout,
            )
            # For ruff format, exit code 1 means files were formatted (success)
            # Only consider it a failure if there were no initial format issues
            if not format_success and initial_format_count > 0:
                format_success = True
        except subprocess.TimeoutExpired:
            timeout_msg = (
                f"Ruff execution timed out ({timeout}s limit exceeded).\n\n"
                "This may indicate:\n"
                "  - Large codebase taking too long to process\n"
                "  - Need to increase timeout via --tool-options ruff:timeout=N"
            )
            return ToolResult(
                name=tool.name,
                success=False,
                output=timeout_msg,
                issues_count=1,  # Count timeout as execution failure
                issues=remaining_issues,  # Include any issues found before timeout
                initial_issues_count=total_initial_count,
                fixed_issues_count=fixed_lint_count,
                remaining_issues_count=1,
            )
        # Formatting fixes are counted separately from lint fixes
        if initial_format_count > 0:
            fixed_count = fixed_lint_count + initial_format_count
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

    # For fmt action, success means we attempted to fix issues
    # We succeed if we fixed at least some issues or had no issues to fix
    # We don't fail just because some issues couldn't be auto-fixed
    overall_success = True

    # Convert initial format files to RuffFormatIssue objects (these were fixed)
    # and combine with remaining issues so formatter can split them by fixability
    fixed_format_issues: list[RuffFormatIssue] = []
    if format_files:
        # Normalize files to absolute paths to keep behavior consistent
        cwd: str | None = tool.get_cwd(paths=python_files)
        for file_path in format_files:
            if cwd and not os.path.isabs(file_path):
                absolute_path = os.path.abspath(os.path.join(cwd, file_path))
                fixed_format_issues.append(RuffFormatIssue(file=absolute_path))
            else:
                fixed_format_issues.append(RuffFormatIssue(file=file_path))

    # Combine fixed format issues with remaining lint issues
    all_issues = fixed_format_issues + remaining_issues

    return ToolResult(
        name=tool.name,
        success=overall_success,
        output=final_output,
        # For fix operations, issues_count represents remaining for summaries
        issues_count=remaining_count,
        # Display both fixed format issues and remaining lint issues
        issues=all_issues,
        initial_issues_count=total_initial_count,
        fixed_issues_count=fixed_count,
        remaining_issues_count=remaining_count,
    )
