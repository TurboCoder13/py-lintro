"""JSON output mode handler for Lintro.

This module provides functionality for running linting tools with JSON output format.
"""

from typing import Any

from lintro.enums.action import Action, normalize_action
from lintro.enums.group_by import normalize_group_by
from lintro.enums.output_format import OutputFormat, normalize_output_format
from lintro.enums.tool_name import ToolName
from lintro.enums.tools_value import ToolsValue
from lintro.models.core.tool_result import ToolResult
from lintro.tools import tool_manager
from lintro.tools.tool_enum import ToolEnum
from lintro.utils.config import load_post_checks_config
from lintro.utils.console_logger import create_logger
from lintro.utils.executor_helpers import (
    _get_tool_display_name,
    _get_tool_lookup_keys,
)
from lintro.utils.output_manager import OutputManager
from lintro.utils.post_checks import execute_post_checks
from lintro.utils.tool_options import parse_tool_options
from lintro.utils.unified_config import UnifiedConfigManager

# Constants
DEFAULT_EXIT_CODE_FAILURE: int = 1


def create_json_output(
    action: str | Action,
    results: list,
    total_issues: int,
    total_fixed: int,
    total_remaining: int,
    exit_code: int,
) -> dict[str, Any]:
    """Create JSON output data structure from tool results.

    Args:
        action: The action being performed (check, fmt, test).
        results: List of tool result objects.
        total_issues: Total number of issues found.
        total_fixed: Total number of issues fixed (only for FIX action).
        total_remaining: Total number of issues remaining (only for FIX action).
        exit_code: Exit code for the run.

    Returns:
        Dictionary containing JSON-serializable results and summary data.
    """
    # Normalize action to Action enum if string
    action_enum = normalize_action(action) if isinstance(action, str) else action

    json_data: dict[str, Any] = {
        "results": [],
        "summary": {
            "total_issues": total_issues,
            "total_fixed": total_fixed if action_enum == Action.FIX else 0,
            "total_remaining": total_remaining if action_enum == Action.FIX else 0,
        },
    }
    for result in results:
        result_data: dict[str, Any] = {
            "tool": result.name,
            "success": getattr(result, "success", True),
            "issues_count": getattr(result, "issues_count", 0),
        }
        if action_enum == Action.FIX:
            result_data["fixed"] = getattr(result, "fixed_issues_count", 0)
            result_data["remaining"] = getattr(
                result,
                "remaining_issues_count",
                0,
            )
        json_data["results"].append(result_data)

    return json_data


def _get_tools_to_run(
    tools: str | ToolsValue | None,
    action: Action,
) -> list[ToolEnum]:
    """Get the list of tools to run based on the tools string and action.

    Args:
        tools: str | ToolsValue | None: Comma-separated tool names, "all", or None.
        action: Action: The action being performed.

    Returns:
        list[ToolEnum]: List of ToolEnum instances to run.

    Raises:
        ValueError: If unknown tool names are provided.
    """
    if tools == ToolsValue.ALL or tools is None:
        if action == Action.FIX:
            available_tools = tool_manager.get_fix_tools()
        else:  # check
            available_tools = tool_manager.get_check_tools()
        return [t for t in available_tools if t != ToolEnum.PYTEST]

    tool_names: list[str] = [name.strip().upper() for name in tools.split(",")]
    tools_to_run: list[ToolEnum] = []

    for name in tool_names:
        if name.lower() == ToolName.PYTEST.value:
            raise ValueError(
                "pytest tool is not available for check/fmt actions. "
                "Use 'lintro test' instead.",
            )
        try:
            tool_enum = ToolEnum[name]
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


def run_lint_tools_with_json(
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
    raw_output: bool,
    run_dir: str | None = None,
) -> int:
    """Run linting tools with JSON output format.

    Args:
        action: str | Action: The action being performed ("check", "fmt", "test").
        paths: list[str]: List of paths to check.
        tools: str | None: Comma-separated list of tools to run.
        tool_options: str | None: Additional tool options.
        exclude: str | None: Patterns to exclude.
        include_venv: bool: Whether to include virtual environments.
        group_by: str: How to group results.
        output_format: str: Output format for results.
        verbose: bool: Whether to enable verbose output.
        raw_output: bool: Whether to show raw tool output.
        run_dir: str | None: Optional run directory path.

    Returns:
        int: Exit code (0 for success, 1 for failures).
    """
    # Normalize action to enum
    action = normalize_action(action)

    # Create OutputManager once, then conditionally override run_dir if provided
    from pathlib import Path

    output_manager = OutputManager()
    if run_dir is None:
        run_dir = str(output_manager.run_dir)
    else:
        # When run_dir is provided, use it consistently for both
        # OutputManager and logger
        run_dir_path = Path(run_dir)
        run_dir_path.mkdir(parents=True, exist_ok=True)
        output_manager.run_dir = run_dir_path

    logger = create_logger(run_dir=run_dir)

    logger.debug(f"Starting {action} command")
    logger.debug(f"Paths: {paths}")
    logger.debug(f"Tools: {tools}")
    logger.debug(f"Run directory: {run_dir}")

    # For JSON output format, we'll collect results and output JSON at the end
    # Normalize enums while maintaining backward compatibility
    output_fmt_enum: OutputFormat = normalize_output_format(output_format)
    _ = normalize_group_by(group_by)  # Validation only - raises on invalid input
    json_output_mode = output_fmt_enum == OutputFormat.JSON

    try:
        # Get tools to run
        try:
            tools_to_run = _get_tools_to_run(tools=tools, action=action)
        except ValueError as e:
            logger.error(str(e))
            logger.save_console_log()
            return DEFAULT_EXIT_CODE_FAILURE

        if not tools_to_run:
            logger.warning("No tools found to run")
            logger.save_console_log()
            return DEFAULT_EXIT_CODE_FAILURE

        # Parse tool options
        tool_option_dict = parse_tool_options(tool_options)

        # Load post-checks config early to exclude those tools from main phase
        post_cfg_early = load_post_checks_config()
        post_enabled_early = bool(post_cfg_early.get("enabled", False))
        post_tools_early: set[str] = (
            {t.lower() for t in (post_cfg_early.get("tools", []) or [])}
            if post_enabled_early
            else set()
        )

        if post_tools_early:
            tools_to_run = [
                t for t in tools_to_run if t.name.lower() not in post_tools_early
            ]

        # If early post-check filtering removed all tools from the main phase,
        # return a failure to signal that nothing was executed in the main run.
        if not tools_to_run:
            logger.warning(
                "All selected tools were filtered out by post-check configuration",
            )
            logger.save_console_log()
            return DEFAULT_EXIT_CODE_FAILURE

        # Print main header (skip for JSON mode)
        if not json_output_mode:
            logger.print_lintro_header()

        all_results: list = []
        total_issues: int = 0
        total_fixed: int = 0
        total_remaining: int = 0

        # Create UnifiedConfigManager once before the loop to avoid
        # repeated initialization
        config_manager = UnifiedConfigManager()

        # Run each tool with rich formatting
        for tool_enum in tools_to_run:
            # Resolve the tool instance; if unavailable, record failure and continue
            try:
                tool = tool_manager.get_tool(tool_enum)
            except Exception as e:
                tool_name: str = _get_tool_display_name(tool_enum)
                logger.warning(f"Tool '{tool_name}' unavailable: {e}")

                all_results.append(
                    ToolResult(
                        name=tool_name,
                        success=False,
                        output=str(e),
                        issues_count=0,
                    ),
                )
                continue

            # Use canonical display name for consistent logging
            tool_name: str = _get_tool_display_name(tool_enum)
            # Print rich tool header (skip for JSON mode)
            if not json_output_mode:
                logger.print_tool_header(tool_name=tool_name, action=action)

            try:
                # Configure tool options using UnifiedConfigManager
                # Priority: CLI --tool-options > [tool.lintro.<tool>] > global settings
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
                    total_fixed += getattr(result, "fixed_issues_count", 0) or 0
                    total_remaining += getattr(result, "remaining_issues_count", 0) or 0

            except Exception as e:
                tool_name: str = _get_tool_display_name(tool_enum)
                logger.warning(f"Tool '{tool_name}' failed: {e}")

                all_results.append(
                    ToolResult(
                        name=tool_name,
                        success=False,
                        output=str(e),
                        issues_count=0,
                    ),
                )

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

        # Output JSON if in JSON mode
        if json_output_mode:
            import json

            json_data = create_json_output(
                action=action,
                results=all_results,
                total_issues=total_issues,
                total_fixed=total_fixed,
                total_remaining=total_remaining,
                exit_code=0,  # Will be set later based on results
            )
            print(json.dumps(json_data, indent=2))

        # Write report files
        output_manager.write_reports_from_results(all_results)

        # Determine exit code
        exit_code = 0
        if action == Action.FIX:
            if total_remaining > 0:
                exit_code = 1
            # Also check for tool failures
            if any(not getattr(r, "success", True) for r in all_results):
                exit_code = 1
        else:  # check
            if total_issues > 0:
                exit_code = 1
            # Also check for tool failures
            if any(not getattr(r, "success", True) for r in all_results):
                exit_code = 1

        return exit_code

    except Exception as e:
        logger.error(f"Error running tools: {e}")
        logger.save_console_log()
        return DEFAULT_EXIT_CODE_FAILURE
