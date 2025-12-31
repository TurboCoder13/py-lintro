"""Helper functions for tool execution.

Clean, straightforward approach using Loguru with rich formatting:
1. OutputManager - handles structured output files only
2. SimpleLintroLogger - handles console display AND logging with Loguru + rich
   formatting
3. No tee, no stream redirection, no complex state management
"""

from lintro.enums.action import Action, normalize_action
from lintro.enums.tool_name import ToolName
from lintro.enums.tools_value import ToolsValue
from lintro.models.core.tool_result import ToolResult
from lintro.tools import tool_manager
from lintro.tools.tool_enum import ToolEnum
from lintro.utils.config import load_post_checks_config
from lintro.utils.output_manager import OutputManager
from lintro.utils.post_checks import execute_post_checks

# Constants
DEFAULT_EXIT_CODE_SUCCESS: int = 0
DEFAULT_EXIT_CODE_FAILURE: int = 1
DEFAULT_REMAINING_COUNT: int = 1

# Mapping from ToolEnum to canonical display names
_TOOL_DISPLAY_NAMES: dict[ToolEnum, str] = {
    ToolEnum.BLACK: "black",
    ToolEnum.DARGLINT: "darglint",
    ToolEnum.HADOLINT: "hadolint",
    ToolEnum.PRETTIER: "prettier",
    ToolEnum.PYTEST: "pytest",
    ToolEnum.RUFF: "ruff",
    ToolEnum.YAMLLINT: "yamllint",
    ToolEnum.ACTIONLINT: "actionlint",
    ToolEnum.BANDIT: "bandit",
}


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
        return _TOOL_DISPLAY_NAMES.get(tool_enum, tool_enum.name.lower())


def _get_tool_lookup_keys(tool_enum: ToolEnum, tool_name: str) -> set[str]:
    """Get all possible lookup keys for a tool in tool_option_dict.

    This includes the tool's display name and enum name (both lowercased).

    Args:
        tool_enum: The ToolEnum instance.
        tool_name: The canonical display name for the tool.

    Returns:
        set[str]: Set of lowercase keys to check in tool_option_dict.
    """
    return {tool_name.lower(), tool_enum.name.lower()}


def _get_tools_to_run(
    tools: str | ToolsValue | None,
    action: str | Action,
) -> list[ToolEnum]:
    """Get the list of tools to run based on the tools string and action.

    Args:
        tools: str | None: Comma-separated tool names, "all", or None.
        action: str: "check", "fmt", or "test".

    Returns:
        list[ToolEnum]: List of ToolEnum instances to run.

    Raises:
        ValueError: If unknown tool names are provided.
    """
    action = normalize_action(action)
    if action == Action.TEST:
        # Test action only supports pytest
        if tools and tools.lower() != "pytest":
            raise ValueError(
                (
                    "Only 'pytest' is supported for the test action; "
                    "run 'lintro test' without --tools or "
                    "use '--tools pytest'"
                ),
            )
        try:
            return [ToolEnum["PYTEST"]]
        except KeyError:
            raise ValueError(
                "pytest tool is not available",
            ) from None

    if tools == ToolsValue.ALL or tools is None:
        # Get all available tools for the action
        if action == Action.FIX:
            available_tools = tool_manager.get_fix_tools()
        else:  # check
            available_tools = tool_manager.get_check_tools()
        # Filter out pytest for check/fmt actions
        return [t for t in available_tools if t.name.upper() != "PYTEST"]

    # Parse specific tools
    tool_names: list[str] = [name.strip().upper() for name in tools.split(",")]
    tools_to_run: list[ToolEnum] = []

    for name in tool_names:
        # Reject pytest for check/fmt actions
        if name == ToolName.PYTEST.value:
            raise ValueError(
                "pytest tool is not available for check/fmt actions. "
                "Use 'lintro test' instead.",
            )
        try:
            tool_enum = ToolEnum[name]
            # Verify the tool supports the requested action
            if action == Action.FIX:
                tool_instance = tool_manager.get_tool(tool_enum)
                if not tool_instance.can_fix:
                    raise ValueError(
                        f"Tool '{name.lower()}' does not support formatting",
                    )
            tools_to_run.append(tool_enum)
        except KeyError:
            available_names: list[str] = [
                e.name.lower() for e in ToolEnum if e.name.upper() != "PYTEST"
            ]
            raise ValueError(
                f"Unknown tool '{name.lower()}'. Available tools: {available_names}",
            ) from None

    return tools_to_run


# Tool options parsing moved to tool_options.py


# Output writing functionality moved to output_writers.py


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
) -> int:
    """Simplified runner using Loguru-based logging with rich formatting.

    Clean approach with beautiful output:
    - SimpleLintroLogger handles ALL console output and file logging with rich
      formatting
    - OutputManager handles structured output files
    - No tee, no complex state management

    Args:
        action: str | Action: Action to perform ("check", "fmt", "test").
        paths: list[str]: List of paths to check.
        tools: str | None: Comma-separated list of tools to run.
        tool_options: str | None: Additional tool options.
        exclude: str | None: Patterns to exclude.
        include_venv: bool: Whether to include virtual environments.
        group_by: str: How to group results.
        output_format: str: Output format for results.
        verbose: bool: Whether to enable verbose output.
        raw_output: bool: Whether to show raw tool output instead of formatted output.
        output_file: str | None: Optional file path to write results to.

    Returns:
        int: Exit code (0 for success, 1 for failures).
    """
    # Normalize action to enum
    action = normalize_action(action)

    # Initialize output manager for this run
    output_manager = OutputManager()

    # Initialize Loguru logging (must happen before any logger.debug() calls)
    from lintro.utils.logger_setup import setup_loguru

    setup_loguru(output_manager.run_dir)

    # Create simplified logger with rich formatting
    from lintro.utils.console_logger import create_logger

    logger = create_logger(run_dir=output_manager.run_dir)

    # Get tools to run
    try:
        tools_to_run = _get_tools_to_run(tools, action)
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
        tools_to_run = [
            t for t in tools_to_run if t.name.lower() not in post_tools_early
        ]

    # If early post-check filtering removed all tools from the main phase,
    # that's okay - post-checks will still run. Just log the situation.
    if not tools_to_run:
        logger.console_output(
            text=(
                "All selected tools are configured as post-checks - "
                "skipping main phase"
            ),
        )

    # Print main header with output directory information
    tools_list: str = ", ".join(t.name.lower() for t in tools_to_run)
    logger.print_lintro_header(
        action=action,
        tool_count=len(tools_to_run),
        tools_list=tools_list,
    )

    # Print verbose info if requested
    if verbose:
        paths_list: str = ", ".join(paths)
        logger.print_verbose_info(
            action=action,
            tools_list=tools_list,
            paths_list=paths_list,
            output_format=output_format,
        )

    # Execute tools and collect results
    all_results = []
    exit_code = 0
    total_issues = 0
    total_fixed = 0
    total_remaining = 0

    # Parse tool options once for all tools
    from lintro.utils.tool_options import parse_tool_options

    tool_option_dict = parse_tool_options(tool_options)

    for tool_enum in tools_to_run:
        try:
            tool = tool_manager.get_tool(tool_enum)
            tool_name = _get_tool_display_name(tool_enum)

            # Print tool header before execution
            logger.print_tool_header(tool_name=tool_name, action=action)

            # Configure tool options using UnifiedConfigManager
            # Priority: CLI --tool-options > [tool.lintro.<tool>] > global settings
            from lintro.utils.unified_config import UnifiedConfigManager

            config_manager = UnifiedConfigManager()

            # Build CLI overrides from --tool-options
            cli_overrides: dict[str, object] = {}
            lookup_keys = _get_tool_lookup_keys(tool_enum, tool_name)
            for option_key in lookup_keys:
                overrides = tool_option_dict.get(option_key)
                if overrides:
                    cli_overrides.update(overrides)

            # Apply unified config with CLI overrides
            config_manager.apply_config_to_tool(
                tool=tool,
                cli_overrides=cli_overrides if cli_overrides else None,
            )

            # Set common options
            if exclude:
                exclude_patterns: list[str] = [
                    pattern.strip() for pattern in exclude.split(",")
                ]
                tool.set_options(exclude_patterns=exclude_patterns)

            tool.set_options(include_venv=include_venv)

            # If Black is configured as a post-check, avoid double formatting by
            # disabling Ruff's formatting stages unless explicitly overridden via
            # CLI or config. This keeps Ruff focused on lint fixes while Black
            # handles formatting.
            if "black" in post_tools_early and tool_name == ToolName.RUFF.value:
                # Get tool config from manager to check for explicit overrides
                tool_config = config_manager.get_tool_config(tool_name)
                lintro_tool_cfg = tool_config.lintro_tool_config or {}
                if action == Action.FIX:
                    if (
                        "format" not in cli_overrides
                        and "format" not in lintro_tool_cfg
                    ):
                        tool.set_options(format=False)
                else:  # check
                    if (
                        "format_check" not in cli_overrides
                        and "format_check" not in lintro_tool_cfg
                    ):
                        tool.set_options(format_check=False)

            # Execute the tool
            result = tool.fix(paths) if action == Action.FIX else tool.check(paths)

            all_results.append(result)

            # Update totals
            total_issues += getattr(result, "issues_count", 0)
            if action == Action.FIX:
                fixed_count = getattr(result, "fixed_issues_count", None)
                total_fixed += fixed_count if fixed_count is not None else 0
                remaining_count = getattr(result, "remaining_issues_count", None)
                total_remaining += remaining_count if remaining_count is not None else 0

            # Use formatted_output if available, otherwise format from issues or output
            display_output: str | None = None
            if result.formatted_output:
                display_output = result.formatted_output
            elif result.issues:
                # Format issues using the tool formatter
                from lintro.utils.output_formatting import format_tool_output

                display_output = format_tool_output(
                    tool_name=tool_name,
                    output=result.output or "",
                    output_format=output_format,
                    issues=list(result.issues),
                )
            elif result.output and raw_output:
                # Use raw output when raw_output flag is True
                display_output = result.output

            # Display the formatted output if available
            if display_output and display_output.strip():
                from lintro.utils.result_formatters import print_tool_result

                def success_func(message: str) -> None:
                    logger.console_output(text=message, color="green")

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

        except Exception as e:
            import traceback

            tool_name = tool_enum.name.lower()
            logger.console_output(f"Error running {tool_name}: {e}")
            logger.console_output(f"Traceback: {traceback.format_exc()}")

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
        except Exception as e:
            logger.console_output(f"Warning: Failed to write reports: {e}")
            # Continue execution - report writing failures should not stop the tool

    # Determine final exit code
    if action == Action.FIX:
        if total_remaining > 0:
            exit_code = 1
    else:  # check
        if total_issues > 0:
            exit_code = 1
        # Also check for tool failures
        if any(not getattr(r, "success", True) for r in all_results):
            exit_code = 1

    return exit_code
