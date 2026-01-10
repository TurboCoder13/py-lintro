"""Helper functions for tool execution.

Clean, straightforward approach using Loguru with rich formatting:
1. OutputManager - handles structured output files only
2. ThreadSafeConsoleLogger - handles console display with thread-safe message
   tracking for parallel execution
3. No tee, no stream redirection, no complex state management

Supports parallel execution when enabled via configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from lintro.enums.action import Action, normalize_action
from lintro.models.core.tool_result import ToolResult
from lintro.tools import tool_manager
from lintro.utils.config import load_post_checks_config
from lintro.utils.execution.exit_codes import (
    DEFAULT_EXIT_CODE_FAILURE,
    DEFAULT_EXIT_CODE_SUCCESS,
    DEFAULT_REMAINING_COUNT,
    aggregate_tool_results,
    determine_exit_code,
)
from lintro.utils.execution.parallel_executor import run_tools_parallel
from lintro.utils.execution.tool_configuration import (
    configure_tool_for_execution,
    get_tool_display_name,
    get_tools_to_run,
)
from lintro.utils.output import OutputManager
from lintro.utils.post_checks import execute_post_checks
from lintro.utils.unified_config import UnifiedConfigManager

if TYPE_CHECKING:
    pass

# Re-export constants for backwards compatibility
__all__ = [
    "DEFAULT_EXIT_CODE_FAILURE",
    "DEFAULT_EXIT_CODE_SUCCESS",
    "DEFAULT_REMAINING_COUNT",
    "run_lint_tools_simple",
]


def run_lint_tools_simple(
    *,
    action: str | Action,
    paths: list[str],
    tools: str | None,
    tool_options: str | None,
    exclude: str | None,
    include_venv: bool,
    group_by: str,
    output_format: str,
    verbose: bool,
    raw_output: bool = False,
    output_file: str | None = None,
    incremental: bool = False,
    debug: bool = False,
) -> int:
    """Simplified runner using Loguru-based logging with rich formatting.

    Clean approach with beautiful output:
    - ThreadSafeConsoleLogger handles ALL console output with thread-safe
      message tracking
    - OutputManager handles structured output files
    - No tee, no complex state management

    Args:
        action: Action to perform ("check", "fmt", "test").
        paths: List of paths to check.
        tools: Comma-separated list of tools to run.
        tool_options: Additional tool options.
        exclude: Patterns to exclude.
        include_venv: Whether to include virtual environments.
        group_by: How to group results.
        output_format: Output format for results.
        verbose: Whether to enable verbose output.
        raw_output: Whether to show raw tool output instead of formatted output.
        output_file: Optional file path to write results to.
        incremental: Whether to only check files changed since last run.
        debug: Whether to show DEBUG messages on console.

    Returns:
        Exit code (0 for success, 1 for failures).

    Raises:
        TypeError: If a programming error occurs during tool execution.
        AttributeError: If a programming error occurs during tool execution.
    """
    # Normalize action to enum
    action = normalize_action(action)

    # Initialize output manager for this run
    output_manager = OutputManager()

    # Initialize Loguru logging (must happen before any logger.debug() calls)
    from lintro.utils.logger_setup import setup_execution_logging

    setup_execution_logging(output_manager.run_dir, debug=debug)

    # Create simplified logger with rich formatting
    from lintro.utils.console import create_logger

    logger = create_logger(run_dir=output_manager.run_dir)

    # Get tools to run
    try:
        tools_to_run = get_tools_to_run(tools, action)
    except ValueError as e:
        logger.console_output(f"Error: {e}")
        return 1

    if not tools_to_run:
        logger.console_output("No tools to run.")
        return 0

    # Load post-checks config early to exclude those tools from main phase
    post_cfg_early = load_post_checks_config()
    post_enabled_early = bool(post_cfg_early.get("enabled", False))
    post_tools_early: set[str] = (
        {t.lower() for t in (post_cfg_early.get("tools", []) or [])}
        if post_enabled_early
        else set()
    )

    # Filter out post-check tools from main phase
    if post_tools_early:
        tools_to_run = [t for t in tools_to_run if t.lower() not in post_tools_early]

    # If early post-check filtering removed all tools from the main phase,
    # that's okay - post-checks will still run. Just log the situation.
    # Track this state so we can return failure if post-checks don't run.
    main_phase_empty_due_to_filter = bool(not tools_to_run and post_tools_early)
    if main_phase_empty_due_to_filter:
        logger.console_output(
            text=(
                "All selected tools are configured as post-checks - "
                "skipping main phase"
            ),
        )

    # Print main header with output directory information
    logger.print_lintro_header()

    # Show incremental mode message
    if incremental:
        logger.console_output(
            text="Incremental mode: only checking files changed since last run",
            color="cyan",
        )

    # Execute tools and collect results
    all_results: list[ToolResult] = []
    exit_code = 0
    total_issues = 0
    total_fixed = 0
    total_remaining = 0

    # Parse tool options once for all tools
    from lintro.utils.tool_options import parse_tool_options

    tool_option_dict = parse_tool_options(tool_options)

    # Create UnifiedConfigManager once before the loop
    config_manager = UnifiedConfigManager()

    # Check if parallel execution is enabled
    from lintro.config.config_loader import get_config

    lintro_config = get_config()
    use_parallel = lintro_config.execution.parallel and len(tools_to_run) > 1

    # Define success_func once before the loop
    def success_func(message: str) -> None:
        logger.console_output(text=message, color="green")

    # Use parallel execution if enabled
    if use_parallel:
        logger.console_output(
            text=f"Running {len(tools_to_run)} tools in parallel "
            f"(max {lintro_config.execution.max_workers} workers)",
        )
        all_results = run_tools_parallel(
            tools_to_run=tools_to_run,
            paths=paths,
            action=action,
            config_manager=config_manager,
            tool_option_dict=tool_option_dict,
            exclude=exclude,
            include_venv=include_venv,
            post_tools=post_tools_early,
            max_workers=lintro_config.execution.max_workers,
            incremental=incremental,
        )

        # Calculate totals from parallel results using helper
        total_issues, total_fixed, total_remaining = aggregate_tool_results(
            all_results,
            action,
        )
        # Check for failures in parallel results
        if any(not result.success for result in all_results):
            exit_code = 1

        # Display results for parallel execution
        for result in all_results:
            # Print tool header like sequential mode does
            display_name = get_tool_display_name(result.name)
            logger.print_tool_header(tool_name=display_name, action=action)

            display_output: str | None = None
            if result.formatted_output:
                display_output = result.formatted_output
            elif result.issues or result.output:
                from lintro.utils.output import format_tool_output

                display_output = format_tool_output(
                    tool_name=result.name,
                    output=result.output or "",
                    output_format=output_format,
                    issues=list(result.issues) if result.issues else None,
                )
            if result.output and raw_output:
                display_output = result.output

            if display_output and display_output.strip():
                from lintro.utils.result_formatters import print_tool_result

                print_tool_result(
                    console_output_func=logger.console_output,
                    success_func=success_func,
                    tool_name=result.name,
                    output=display_output,
                    issues_count=result.issues_count,
                    raw_output_for_meta=result.output,
                    action=action,
                    success=result.success,
                )
            elif result.issues_count == 0 and result.success:
                logger.console_output(
                    text="✓ No issues found.",
                    color="green",
                )

    else:
        # Sequential execution (original behavior)
        for tool_name in tools_to_run:
            try:
                tool = tool_manager.get_tool(tool_name)
                display_name = get_tool_display_name(tool_name)

                # Print tool header before execution
                logger.print_tool_header(tool_name=display_name, action=action)

                # Configure tool using shared helper
                configure_tool_for_execution(
                    tool=tool,
                    tool_name=tool_name,
                    config_manager=config_manager,
                    tool_option_dict=tool_option_dict,
                    exclude=exclude,
                    include_venv=include_venv,
                    incremental=incremental,
                    action=action,
                    post_tools=post_tools_early,
                )

                # Execute the tool
                result = (
                    tool.fix(paths, {})
                    if action == Action.FIX
                    else tool.check(paths, {})
                )

                all_results.append(result)

                # Update totals
                total_issues += getattr(result, "issues_count", 0)
                if action == Action.FIX:
                    fixed_count = getattr(result, "fixed_issues_count", None)
                    total_fixed += fixed_count if fixed_count is not None else 0
                    remaining_count = getattr(result, "remaining_issues_count", None)
                    total_remaining += (
                        remaining_count if remaining_count is not None else 0
                    )

                # Use formatted_output if available, otherwise format from issues
                display_output = None
                if result.formatted_output:
                    display_output = result.formatted_output
                elif result.issues or result.output:
                    # Format issues using the tool formatter
                    # Also format when there's output (e.g., coverage) even with no
                    # issues
                    from lintro.utils.output import format_tool_output

                    display_output = format_tool_output(
                        tool_name=tool_name,
                        output=result.output or "",
                        output_format=output_format,
                        issues=list(result.issues) if result.issues else None,
                    )
                if result.output and raw_output:
                    # Use raw output when raw_output flag is True (overrides formatted)
                    display_output = result.output

                # Display the formatted output if available
                if display_output and display_output.strip():
                    from lintro.utils.result_formatters import print_tool_result

                    print_tool_result(
                        console_output_func=logger.console_output,
                        success_func=success_func,
                        tool_name=tool_name,
                        output=display_output,
                        issues_count=result.issues_count,
                        raw_output_for_meta=result.output,
                        action=action,
                        success=result.success,
                    )
                elif result.issues_count == 0 and result.success:
                    # Show success message when no issues found and no output
                    logger.console_output(text="Processing files")
                    logger.console_output(text="✓ No issues found.", color="green")
                    logger.console_output(text="")

                # Set exit code based on success
                if not result.success:
                    exit_code = 1

            except (TypeError, AttributeError):
                # Programming errors should be re-raised for debugging
                from loguru import logger as loguru_logger

                loguru_logger.exception(f"Programming error running {tool_name}")
                raise
            except (OSError, ValueError, RuntimeError) as e:
                from loguru import logger as loguru_logger

                # Log full exception with traceback to debug.log via loguru
                loguru_logger.exception(f"Error running {tool_name}")
                # Show user-friendly error message on console
                logger.console_output(f"Error running {tool_name}: {e}")

                # Create a failed result for this tool
                failed_result = ToolResult(
                    name=tool_name,
                    success=False,
                    output=f"Failed to initialize tool: {e}",
                    issues_count=0,
                )
                all_results.append(failed_result)
                exit_code = 1

    # Execute post-checks if configured
    total_issues, total_fixed, total_remaining = execute_post_checks(
        action=action,
        paths=paths,
        exclude=exclude,
        include_venv=include_venv,
        group_by=group_by,
        output_format=output_format,
        verbose=verbose,
        raw_output=raw_output,
        logger=logger,
        all_results=all_results,
        total_issues=total_issues,
        total_fixed=total_fixed,
        total_remaining=total_remaining,
    )

    # Display results
    if all_results:
        if output_format.lower() == "json":
            # Output JSON to stdout
            import json

            from lintro.utils.json_output import create_json_output

            json_data = create_json_output(
                action=str(action),
                results=all_results,
                total_issues=total_issues,
                total_fixed=total_fixed,
                total_remaining=total_remaining,
                exit_code=exit_code,
            )
            print(json.dumps(json_data, indent=2))
        else:
            logger.print_execution_summary(action, all_results)

        # Write report files (markdown, html, csv)
        try:
            output_manager.write_reports_from_results(all_results)
        except (OSError, ValueError, TypeError) as e:
            logger.console_output(f"Warning: Failed to write reports: {e}")
            # Continue execution - report writing failures should not stop the tool

    # Determine final exit code using helper
    return determine_exit_code(
        action=action,
        all_results=all_results,
        total_issues=total_issues,
        total_remaining=total_remaining,
        main_phase_empty_due_to_filter=main_phase_empty_due_to_filter,
    )
