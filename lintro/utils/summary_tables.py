"""Summary table generation for Lintro tool output.

Handles formatting and display of execution summary tables with tabulate.
"""

import contextlib
from collections.abc import Callable, Sequence
from typing import Any

from lintro.enums.action import Action
from lintro.enums.tool_name import ToolName, normalize_tool_name
from lintro.utils.console import (
    RE_CANNOT_AUTOFIX,
    RE_REMAINING_OR_CANNOT,
    get_summary_value,
    get_tool_emoji,
)

# Constants
DEFAULT_REMAINING_COUNT: str = "?"


def _extract_skip_reason(output: str) -> str:
    """Extract abbreviated skip reason from tool output.

    Skip messages have format: "Skipping {tool}: {error}. Minimum required: ..."

    Args:
        output: The tool output containing the skip message.

    Returns:
        Abbreviated reason string for display in the summary table.
    """
    if ":" in output and ". Minimum" in output:
        colon_idx = output.index(":")
        minimum_idx = output.index(". Minimum")
        # Ensure colon comes before ". Minimum" to get a valid slice
        if colon_idx >= minimum_idx:
            return "SKIPPED"
        start = colon_idx + 1
        end = minimum_idx
        reason = output[start:end].strip()
        # Abbreviate common error messages
        if "Command failed" in reason:
            return "Cmd failed"
        if "Could not parse version" in reason:
            return "No version"
        if "below minimum" in reason:
            return "Outdated"
        if "Failed to run" in reason:
            return "Not found"
        # Truncate if too long
        return reason[:20] if len(reason) > 20 else reason
    return "SKIPPED"


def _safe_cast(
    summary: dict[str, Any],
    key: str,
    default: int | float,
    converter: Callable[[Any], int | float],
) -> int | float:
    """Safely extract and cast a value from a summary dictionary.

    Args:
        summary: Dictionary containing summary data.
        key: Key to extract from summary.
        default: Default value if extraction/conversion fails.
        converter: Function to convert the extracted value (e.g., int, float).

    Returns:
        Converted value or default if extraction/conversion fails.
    """
    try:
        return converter(get_summary_value(summary, key, default))
    except (ValueError, TypeError):
        return default


def _format_tool_display_name(tool_name: str) -> str:
    """Format tool name for display (convert underscores to hyphens).

    Args:
        tool_name: Raw tool name (may contain underscores).

    Returns:
        Display name with hyphens instead of underscores.
    """
    return tool_name.replace("_", "-")


def print_summary_table(
    console_output_func: Callable[..., None],
    action: Action,
    tool_results: Sequence[object],
) -> None:
    """Print the summary table for the run.

    Args:
        console_output_func: Function to output text to console
        action: The action being performed.
        tool_results: Sequence of tool results.
    """
    try:
        from tabulate import tabulate

        # Sort results alphabetically by tool name for consistent output
        sorted_results = sorted(
            tool_results,
            key=lambda r: getattr(r, "name", "unknown").lower(),
        )

        summary_data: list[list[str]] = []
        for result in sorted_results:
            tool_name: str = getattr(result, "name", "unknown")
            issues_count: int = getattr(result, "issues_count", 0)
            success: bool = getattr(result, "success", True)

            emoji: str = get_tool_emoji(tool_name)
            display_name: str = _format_tool_display_name(tool_name)
            tool_display: str = f"{emoji} {display_name}"

            # Special handling for pytest/test action
            # Safely check if this is pytest by normalizing the tool name
            is_pytest = False
            with contextlib.suppress(ValueError):
                is_pytest = normalize_tool_name(tool_name) == ToolName.PYTEST

            if action == Action.TEST and is_pytest:
                pytest_summary = getattr(result, "pytest_summary", None)
                if pytest_summary:
                    # Use pytest summary data for more detailed display
                    passed = _safe_cast(pytest_summary, "passed", 0, int)
                    failed = _safe_cast(pytest_summary, "failed", 0, int)
                    skipped = _safe_cast(pytest_summary, "skipped", 0, int)
                    duration = _safe_cast(pytest_summary, "duration", 0.0, float)
                    total = _safe_cast(pytest_summary, "total", 0, int)

                    # Create detailed status display
                    status_display = (
                        "\033[92m✅ PASS\033[0m"  # green
                        if failed == 0
                        else "\033[91m❌ FAIL\033[0m"  # red
                    )

                    # Format duration with proper units
                    duration_str = f"{duration:.2f}s"

                    # Create row with separate columns for each metric
                    summary_data.append(
                        [
                            tool_display,
                            status_display,
                            str(passed),
                            str(failed),
                            str(skipped),
                            str(total),
                            duration_str,
                        ],
                    )
                    continue

            # Handle TEST action for non-pytest tools
            if action == Action.TEST:
                # Non-pytest tool in test mode - show basic pass/fail
                status_display = (
                    "\033[92m✅ PASS\033[0m"
                    if (success and issues_count == 0)
                    else "\033[91m❌ FAIL\033[0m"
                )
                summary_data.append(
                    [
                        tool_display,
                        status_display,
                        "-",  # Passed
                        "-",  # Failed
                        "-",  # Skipped
                        "-",  # Total
                        "-",  # Duration
                    ],
                )
                continue

            # For format operations, success means tool ran
            # (regardless of fixes made)
            # For check operations, success means no issues found
            if action == Action.FIX:
                # Format operations: show fixed count and remaining status
                if success:
                    status_display = "\033[92m✅ PASS\033[0m"  # green
                else:
                    status_display = "\033[91m❌ FAIL\033[0m"  # red

                # Get result output for parsing
                # Note: "No files to fix" means the tool ran successfully but
                # found no files - this is PASS with 0 fixed/remaining, not SKIPPED
                # (consistent with check mode behavior)
                result_output: str = getattr(result, "output", "")

                # Prefer standardized counts from ToolResult
                remaining_std = getattr(result, "remaining_issues_count", None)
                fixed_std = getattr(result, "fixed_issues_count", None)

                if remaining_std is not None:
                    try:
                        remaining_count: int | str = int(remaining_std)
                    except (ValueError, TypeError):
                        remaining_count = DEFAULT_REMAINING_COUNT
                else:
                    # Parse output to determine remaining issues
                    remaining_count = 0
                    if result_output and (
                        "remaining" in result_output.lower()
                        or "cannot be auto-fixed" in result_output.lower()
                    ):
                        # Try multiple patterns to match different
                        # output formats
                        remaining_match = RE_CANNOT_AUTOFIX.search(
                            result_output,
                        )
                        if not remaining_match:
                            remaining_match = RE_REMAINING_OR_CANNOT.search(
                                result_output.lower(),
                            )
                        if remaining_match:
                            try:
                                remaining_count = int(remaining_match.group(1))
                            except (ValueError, TypeError):
                                remaining_count = DEFAULT_REMAINING_COUNT
                        elif not success:
                            remaining_count = DEFAULT_REMAINING_COUNT

                if fixed_std is not None:
                    try:
                        fixed_display_value = int(fixed_std)
                    except (ValueError, TypeError):
                        fixed_display_value = 0
                else:
                    # Fall back to issues_count when fixed is unknown
                    try:
                        fixed_display_value = int(issues_count)
                    except (ValueError, TypeError):
                        fixed_display_value = 0

                # Fixed issues display
                fixed_display: str = f"\033[92m{fixed_display_value}\033[0m"  # green

                # Remaining issues display
                if isinstance(remaining_count, str):
                    # Display sentinel value verbatim
                    remaining_display: str = (
                        f"\033[93m{remaining_count}\033[0m"  # yellow
                    )
                else:
                    remaining_display = (
                        f"\033[91m{remaining_count}\033[0m"  # red
                        if remaining_count > 0
                        else f"\033[92m{remaining_count}\033[0m"  # green
                    )
            else:  # check
                # Check if this is an execution failure (timeout/error)
                # vs linting issues
                result_output = getattr(result, "output", "") or ""

                # Check if tool was skipped (version check failure, etc.)
                # Only mark as skipped if the output matches the version check
                # failure pattern: "Skipping {tool_name}: ..." (case-insensitive)
                # This prevents false positives when tools output "skipping"
                # in their own messages
                is_skipped = (
                    result_output
                    and isinstance(result_output, str)
                    and result_output.lower().startswith(
                        f"skipping {tool_name.lower()}:",
                    )
                )

                has_execution_failure = result_output and (
                    "timeout" in result_output.lower()
                    or "error processing" in result_output.lower()
                    or "tool execution failed" in result_output.lower()
                )

                # If tool was skipped (version check failure, etc.), show SKIPPED status
                # Note: "No files to check" means the tool ran successfully but found
                # no files - this should be PASS, not SKIPPED
                if is_skipped:
                    status_display = "\033[93m⏭️  SKIPPED\033[0m"  # yellow
                    skip_reason = _extract_skip_reason(result_output)
                    issues_display = f"\033[93m{skip_reason}\033[0m"  # yellow
                # If there are execution failures but no parsed issues,
                # show special status
                elif has_execution_failure and issues_count == 0:
                    # This shouldn't happen with our fix, but handle gracefully
                    status_display = "\033[91m❌ FAIL\033[0m"  # red
                    issues_display = "\033[91mERROR\033[0m"  # red
                elif not success and issues_count == 0:
                    # Execution failure with no issues parsed - show as failure
                    status_display = "\033[91m❌ FAIL\033[0m"  # red
                    issues_display = "\033[91mERROR\033[0m"  # red
                else:
                    status_display = (
                        "\033[92m✅ PASS\033[0m"  # green
                        if (success and issues_count == 0)
                        else "\033[91m❌ FAIL\033[0m"  # red
                    )
                    # Display issues count (0 means PASS, >0 means FAIL)
                    # Note: "No files to check" means the tool ran successfully
                    # but found no files - this is PASS with 0 issues, not SKIPPED
                    issues_display = (
                        f"\033[92m{issues_count}\033[0m"  # green
                        if issues_count == 0
                        else f"\033[91m{issues_count}\033[0m"  # red
                    )
            if action == Action.FIX:
                summary_data.append(
                    [
                        tool_display,
                        status_display,
                        fixed_display,
                        remaining_display,
                    ],
                )
            else:
                summary_data.append([tool_display, status_display, issues_display])

        # Set headers based on action
        # Use plain headers to avoid ANSI/emojis width misalignment
        headers: list[str]
        if action == Action.TEST:
            # Special table for test action with separate columns for test metrics
            headers = [
                "Tool",
                "Status",
                "Passed",
                "Failed",
                "Skipped",
                "Total",
                "Duration",
            ]
        elif action == Action.FIX:
            headers = ["Tool", "Status", "Fixed", "Remaining"]
        else:
            headers = ["Tool", "Status", "Issues"]

        # Render with plain values to ensure proper alignment across terminals
        table: str = tabulate(
            tabular_data=summary_data,
            headers=headers,
            tablefmt="grid",
            stralign="left",
            disable_numparse=True,
        )
        console_output_func(text=table)
        console_output_func(text="")

    except ImportError:
        # Fallback if tabulate not available
        console_output_func(text="Summary table requires tabulate package")
