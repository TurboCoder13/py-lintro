"""Post-check execution utilities.

Handles optional post-check tools that run after primary linting tools.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from lintro.enums.action import Action
from lintro.enums.group_by import normalize_group_by
from lintro.enums.output_format import OutputFormat, normalize_output_format
from lintro.tools import tool_manager
from lintro.tools.tool_enum import ToolEnum
from lintro.utils.config import load_post_checks_config
from lintro.utils.output_formatting import format_tool_output
from lintro.utils.unified_config import UnifiedConfigManager

if TYPE_CHECKING:
    from lintro.models.core.tool_result import ToolResult
    from lintro.utils.console_logger import ConsoleLogger


def _get_tool_display_name(tool_enum: ToolEnum) -> str:
    """Get the canonical display name for a tool enum.

    This function provides a consistent mapping from ToolEnum to user-friendly
    display names. It first attempts to get the tool instance to use its canonical
    name, but falls back to a predefined mapping if the tool cannot be instantiated.

    Args:
        tool_enum: The ToolEnum instance.

    Returns:
        str: The canonical display name for the tool.
    """
    # Try to get the tool instance to use its canonical name
    try:
        tool = tool_manager.get_tool(tool_enum)
        return tool.name
    except Exception:
        # Fall back to predefined mapping if tool cannot be instantiated
        return tool_enum.name.lower()


def execute_post_checks(
    *,
    action: Action,
    paths: list[str],
    exclude: str | None,
    include_venv: bool,
    group_by: str,
    output_format: str,
    verbose: bool,
    raw_output: bool,
    logger: ConsoleLogger,
    all_results: list[ToolResult],
    total_issues: int,
    total_fixed: int,
    total_remaining: int,
) -> tuple[int, int, int]:
    """Execute post-check tools after primary linting.

    Args:
        action: Action: The action being performed.
        paths: list[str]: List of paths to check.
        exclude: str | None: Patterns to exclude.
        include_venv: bool: Whether to include virtual environments.
        group_by: str: How to group results.
        output_format: str: Output format for results.
        verbose: bool: Whether to enable verbose output.
        raw_output: bool: Whether to show raw tool output.
        logger: Logger instance for output.
        all_results: list: List to append results to.
        total_issues: int: Current total issues count.
        total_fixed: int: Current total fixed count.
        total_remaining: int: Current total remaining count.

    Returns:
        tuple[int, int, int]: Updated (total_issues, total_fixed, total_remaining)
    """
    # Skip post-checks for test action - test is independent from linting/formatting
    if action == Action.TEST:
        return (total_issues, total_fixed, total_remaining)

    # Normalize enums while maintaining backward compatibility
    output_fmt_enum: OutputFormat = normalize_output_format(output_format)
    _ = normalize_group_by(group_by)  # Normalize for validation, return value unused
    json_output_mode = output_fmt_enum == OutputFormat.JSON

    # Load post-checks config
    post_cfg = load_post_checks_config()
    post_enabled = bool(post_cfg.get("enabled", False))
    post_tools = list(post_cfg.get("tools", [])) if post_enabled else []
    enforce_failure = bool(post_cfg.get("enforce_failure", action == Action.CHECK))

    # In JSON mode, we still need exit-code enforcement even if we skip
    # rendering post-check outputs. If a post-check tool is unavailable
    # and enforce_failure is enabled during check, append a failure result
    # so summaries and exit codes reflect the condition.
    if post_tools and json_output_mode and action == Action.CHECK and enforce_failure:
        for post_tool_name in post_tools:
            try:
                tool_enum = ToolEnum[post_tool_name.upper()]
                # Ensure tool can be resolved; we don't execute it in JSON mode
                _ = tool_manager.get_tool(tool_enum)
            except Exception as e:
                from lintro.models.core.tool_result import ToolResult

                all_results.append(
                    ToolResult(
                        name=post_tool_name,
                        success=False,
                        output=str(e),
                        issues_count=1,
                    ),
                )

    if post_tools:
        # Print a clear post-checks section header (only when not in JSON mode)
        if not json_output_mode:
            logger.print_post_checks_header()

        for post_tool_name in post_tools:
            try:
                tool_enum = ToolEnum[post_tool_name.upper()]
            except KeyError:
                logger.console_output(
                    text=f"Warning: Unknown post-check tool: {post_tool_name}",
                    color="yellow",
                )
                continue

            # If the tool isn't available in the current environment (e.g., unit
            # tests that stub a limited set of tools), skip without enforcing
            # failure. Post-checks are optional when the tool cannot be resolved
            # from the tool manager.
            try:
                tool = tool_manager.get_tool(tool_enum)
            except Exception as e:
                logger.console_output(
                    text=f"Warning: Post-check '{post_tool_name}' unavailable: {e}",
                    color="yellow",
                )
                continue
            # Use canonical display name for consistent logging
            tool_name = _get_tool_display_name(tool_enum)

            # Post-checks run with explicit headers (reuse standard header)
            if not json_output_mode:
                logger.print_tool_header(tool_name=tool_name, action=action)

            try:
                # Configure post-check tool using UnifiedConfigManager
                # This replaces manual sync logic with unified config management
                post_config_manager = UnifiedConfigManager()
                post_config_manager.apply_config_to_tool(tool=tool)

                tool.set_options(include_venv=include_venv)
                if exclude:
                    exclude_patterns: list[str] = [
                        p.strip() for p in exclude.split(",")
                    ]
                    tool.set_options(exclude_patterns=exclude_patterns)

                # For check: Black should run in check mode; for fmt: run fix
                if action == Action.FIX and tool.can_fix:
                    result = tool.fix(paths=paths)
                    issues_count = getattr(result, "issues_count", 0)
                    fixed_count = getattr(result, "fixed_issues_count", None)
                    total_fixed += fixed_count if fixed_count is not None else 0
                    remaining_count = getattr(result, "remaining_issues_count", None)
                    total_remaining += (
                        remaining_count if remaining_count is not None else issues_count
                    )
                else:
                    result = tool.check(paths=paths)
                    issues_count = getattr(result, "issues_count", 0)
                    total_issues += issues_count

                # Format and display output
                output = getattr(result, "output", None)
                issues = getattr(result, "issues", None)
                formatted_output: str = ""
                if (output and output.strip()) or issues:
                    formatted_output = format_tool_output(
                        tool_name=tool_name,
                        output=output or "",
                        output_format=output_fmt_enum.value,
                        issues=issues,
                    )

                if not json_output_mode:
                    from lintro.utils.result_formatters import print_tool_result

                    def success_func(message: str) -> None:
                        logger.console_output(text=message, color="green")

                    if formatted_output and formatted_output.strip():
                        print_tool_result(
                            console_output_func=logger.console_output,
                            success_func=success_func,
                            tool_name=tool_name,
                            output=(
                                formatted_output if not raw_output else (output or "")
                            ),
                            issues_count=issues_count,
                            raw_output_for_meta=output,
                            action=action,
                            success=getattr(result, "success", None),
                        )
                    elif issues_count == 0 and getattr(result, "success", True):
                        # Show success message when no issues found
                        logger.console_output(text="Processing files")
                        logger.console_output(text="✓ No issues found.", color="green")
                        logger.console_output(text="")

                all_results.append(result)
            except Exception as e:
                # Do not crash the entire run due to missing optional post-check
                # tool
                logger.console_output(
                    text=f"Warning: Post-check '{post_tool_name}' failed: {e}",
                    color="yellow",
                )
                # Only enforce failure when the tool was available and executed
                if enforce_failure and action == Action.CHECK:
                    from lintro.models.core.tool_result import ToolResult

                    all_results.append(
                        ToolResult(
                            name=post_tool_name,
                            success=False,
                            output=str(e),
                            issues_count=1,
                        ),
                    )

    return total_issues, total_fixed, total_remaining
