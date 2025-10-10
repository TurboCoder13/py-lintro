"""Simplified runner for lintro commands.

Clean, straightforward approach using Loguru with rich formatting:
1. OutputManager - handles structured output files only
2. SimpleLintroLogger - handles console display AND logging with Loguru + rich
   formatting
3. No tee, no stream redirection, no complex state management
"""

from lintro.enums.group_by import GroupBy, normalize_group_by
from lintro.enums.output_format import OutputFormat, normalize_output_format
from lintro.tools import tool_manager
from lintro.tools.tool_enum import ToolEnum
from lintro.utils.config import load_lintro_tool_config, load_post_checks_config
from lintro.utils.console_logger import create_logger
from lintro.utils.output_manager import OutputManager
from lintro.utils.tool_utils import format_tool_output

# Constants
DEFAULT_EXIT_CODE_SUCCESS: int = 0
DEFAULT_EXIT_CODE_FAILURE: int = 1
DEFAULT_REMAINING_COUNT: int = 1


def _get_tools_to_run(
    tools: str | None,
    action: str,
) -> list[ToolEnum]:
    """Get the list of tools to run based on the tools string and action.

    Args:
        tools: str | None: Comma-separated tool names, "all", or None.
        action: str: "check" or "fmt".

    Returns:
        list[ToolEnum]: List of ToolEnum instances to run.

    Raises:
        ValueError: If unknown tool names are provided.
    """
    if tools == "all" or tools is None:
        # Get all available tools for the action
        if action == "fmt":
            available_tools = tool_manager.get_fix_tools()
        else:  # check
            available_tools = tool_manager.get_check_tools()
        return list(available_tools.keys())

    # Parse specific tools
    tool_names: list[str] = [name.strip().upper() for name in tools.split(",")]
    tools_to_run: list[ToolEnum] = []

    for name in tool_names:
        try:
            tool_enum = ToolEnum[name]
            # Verify the tool supports the requested action
            if action == "fmt":
                tool_instance = tool_manager.get_tool(tool_enum)
                if not tool_instance.can_fix:
                    raise ValueError(
                        f"Tool '{name.lower()}' does not support formatting",
                    )
            tools_to_run.append(tool_enum)
        except KeyError:
            available_names: list[str] = [e.name.lower() for e in ToolEnum]
            raise ValueError(
                f"Unknown tool '{name.lower()}'. Available tools: {available_names}",
            ) from None

    return tools_to_run


def _coerce_value(raw: str) -> object:
    """Coerce a raw CLI value into a typed Python value.

    Rules:
    - "all"/"none" (case-insensitive) -> list[str]
    - "True"/"False" (case-insensitive) -> bool
    - "None"/"null" (case-insensitive) -> None
    - integer (e.g., 88) -> int
    - float (e.g., 0.75) -> float
    - list via pipe-delimited values (e.g., "E|F|W") -> list[str]
      Pipe is chosen to avoid conflict with the top-level comma separator.
    - otherwise -> original string

    Args:
        raw: str: Raw CLI value to coerce.

    Returns:
        object: Coerced value.
    """
    s = raw.strip()
    # Lists via pipe (e.g., select=E|F)
    if "|" in s:
        return [part.strip() for part in s.split("|") if part.strip()]

    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in {"none", "null"}:
        return None

    # Try int
    try:
        return int(s)
    except ValueError:
        pass

    # Try float
    try:
        return float(s)
    except ValueError:
        pass

    return s


def _parse_tool_options(tool_options: str | None) -> dict[str, dict[str, object]]:
    """Parse tool options string into a typed dictionary.

    Args:
        tool_options: str | None: String in format
            "tool:option=value,tool2:option=value". Multiple values for a single
            option can be provided using pipe separators (e.g., select=E|F).

    Returns:
        dict[str, dict[str, object]]: Mapping tool names to typed options.
    """
    if not tool_options:
        return {}

    tool_option_dict: dict[str, dict[str, object]] = {}
    for opt in tool_options.split(","):
        opt = opt.strip()
        if not opt:
            continue
        if ":" not in opt:
            # Skip malformed fragment
            continue
        tool_name, tool_opt = opt.split(":", 1)
        if "=" not in tool_opt:
            # Skip malformed fragment
            continue
        opt_name, opt_value = tool_opt.split("=", 1)
        tool_name = tool_name.strip()
        opt_name = opt_name.strip()
        opt_value = opt_value.strip()
        if not tool_name or not opt_name:
            continue
        if tool_name not in tool_option_dict:
            tool_option_dict[tool_name] = {}
        tool_option_dict[tool_name][opt_name] = _coerce_value(opt_value)

    return tool_option_dict


def run_lint_tools_simple(
    *,
    action: str,
    paths: list[str],
    tools: str | None,
    tool_options: str | None,
    exclude: str | None,
    include_venv: bool,
    group_by: str,
    output_format: str,
    verbose: bool,
    raw_output: bool = False,
) -> int:
    """Simplified runner using Loguru-based logging with rich formatting.

    Clean approach with beautiful output:
    - SimpleLintroLogger handles ALL console output and file logging with rich
      formatting
    - OutputManager handles structured output files
    - No tee, no complex state management

    Args:
        action: str: "check" or "fmt".
        paths: list[str]: List of paths to check.
        tools: str | None: Comma-separated list of tools to run.
        tool_options: str | None: Additional tool options.
        exclude: str | None: Patterns to exclude.
        include_venv: bool: Whether to include virtual environments.
        group_by: str: How to group results.
        output_format: str: Output format for results.
        verbose: bool: Whether to enable verbose output.
        raw_output: bool: Whether to show raw tool output instead of formatted output.

    Returns:
        int: Exit code (0 for success, 1 for failures).
    """
    # Initialize output manager for this run
    output_manager = OutputManager()
    run_dir: str = output_manager.run_dir

    # Create simplified logger with rich formatting
    logger = create_logger(run_dir=run_dir, verbose=verbose, raw_output=raw_output)

    logger.debug(f"Starting {action} command")
    logger.debug(f"Paths: {paths}")
    logger.debug(f"Tools: {tools}")
    logger.debug(f"Run directory: {run_dir}")

    # For JSON output format, we'll collect results and output JSON at the end
    # Normalize enums while maintaining backward compatibility
    output_fmt_enum: OutputFormat = normalize_output_format(output_format)
    group_by_enum: GroupBy = normalize_group_by(group_by)
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
        tool_option_dict = _parse_tool_options(tool_options)

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
        tools_list: str = ", ".join(t.name.lower() for t in tools_to_run)
        if not json_output_mode:
            logger.print_lintro_header(
                action=action,
                tool_count=len(tools_to_run),
                tools_list=tools_list,
            )

            # Print verbose info if requested
            paths_list: str = ", ".join(paths)
            logger.print_verbose_info(
                action=action,
                tools_list=tools_list,
                paths_list=paths_list,
                output_format=output_format,
            )

        all_results: list = []
        total_issues: int = 0
        total_fixed: int = 0
        total_remaining: int = 0

        # Run each tool with rich formatting
        for tool_enum in tools_to_run:
            tool_name: str = tool_enum.name.lower()
            # Resolve the tool instance; if unavailable, record failure and continue
            try:
                tool = tool_manager.get_tool(tool_enum)
            except Exception as e:
                logger.warning(f"Tool '{tool_name}' unavailable: {e}")
                from lintro.models.core.tool_result import ToolResult

                all_results.append(
                    ToolResult(
                        name=tool_name,
                        success=False,
                        output=str(e),
                        issues_count=0,
                    ),
                )
                continue

            # Print rich tool header (skip for JSON mode)
            if not json_output_mode:
                logger.print_tool_header(tool_name=tool_name, action=action)

            try:
                # Configure tool options
                # 1) Load config from pyproject.toml / lintro.toml
                cfg: dict = load_lintro_tool_config(tool_name)
                if cfg:
                    try:
                        tool.set_options(**cfg)
                    except Exception as e:
                        logger.debug(f"Ignoring invalid config for {tool_name}: {e}")
                # 2) CLI --tool-options overrides config file
                if tool_name in tool_option_dict:
                    tool.set_options(**tool_option_dict[tool_name])

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
                if "black" in post_tools_early and tool_name == "ruff":
                    # Respect explicit overrides from CLI or config
                    cli_overrides = tool_option_dict.get("ruff", {})
                    cfg_overrides = cfg or {}
                    if action == "fmt":
                        if (
                            "format" not in cli_overrides
                            and "format" not in cfg_overrides
                        ):
                            tool.set_options(format=False)
                    else:  # check
                        if (
                            "format_check" not in cli_overrides
                            and "format_check" not in cfg_overrides
                        ):
                            tool.set_options(format_check=False)

                # Run the tool
                logger.debug(f"Executing {tool_name}")

                if action == "fmt":
                    # Respect tool defaults; allow overrides via --tool-options
                    result = tool.fix(paths=paths)
                    # Prefer standardized counters when present
                    fixed_count: int = (
                        getattr(result, "fixed_issues_count", None)
                        if hasattr(result, "fixed_issues_count")
                        else None
                    )
                    if fixed_count is None:
                        fixed_count = 0
                    total_fixed += fixed_count

                    remaining_count: int = (
                        getattr(result, "remaining_issues_count", None)
                        if hasattr(result, "remaining_issues_count")
                        else None
                    )
                    if remaining_count is None:
                        # Fallback to issues_count if standardized field absent
                        remaining_count = getattr(result, "issues_count", 0)
                    total_remaining += max(0, remaining_count)

                    # For display in per-tool logger call below
                    issues_count: int = remaining_count
                else:  # check
                    result = tool.check(paths=paths)
                    issues_count = getattr(result, "issues_count", 0)
                    total_issues += issues_count

                # Format and display output
                output = getattr(result, "output", None)
                issues = getattr(result, "issues", None)
                formatted_output: str = ""

                # Call format_tool_output if we have output or issues
                if (output and output.strip()) or issues:
                    formatted_output = format_tool_output(
                        tool_name=tool_name,
                        output=output or "",
                        group_by=group_by_enum.value,
                        output_format=output_fmt_enum.value,
                        issues=issues,
                    )

                # Print tool results with rich formatting (skip for JSON mode)
                if not json_output_mode:
                    # Use raw output if raw_output is true, otherwise use
                    # formatted output
                    display_output = output if raw_output else formatted_output
                    logger.print_tool_result(
                        tool_name=tool_name,
                        output=display_output,
                        issues_count=issues_count,
                        raw_output_for_meta=output,
                        action=action,
                        success=getattr(result, "success", None),
                    )

                # Store result
                all_results.append(result)

                if action == "fmt":
                    # Pull standardized counts again for debug log
                    fixed_dbg = getattr(result, "fixed_issues_count", fixed_count)
                    remaining_dbg = getattr(
                        result,
                        "remaining_issues_count",
                        issues_count,
                    )
                    logger.debug(
                        f"Completed {tool_name}: {fixed_dbg} fixed, "
                        f"{remaining_dbg} remaining",
                    )
                else:
                    logger.debug(f"Completed {tool_name}: {issues_count} issues found")

            except Exception as e:
                logger.error(f"Error running {tool_name}: {e}")
                # Record a failure result and continue so that structured output
                # (e.g., JSON) is still produced even if a tool cannot be
                # resolved or executed. This keeps behavior consistent with tests
                # that validate JSON output presence independent of exit codes.
                from lintro.models.core.tool_result import ToolResult

                all_results.append(
                    ToolResult(
                        name=tool_name,
                        success=False,
                        output=str(e),
                        issues_count=0,
                    ),
                )
                # Continue to next tool rather than aborting the entire run
                continue

        # Optionally run post-checks (explicit, after main tools)
        post_cfg = post_cfg_early or load_post_checks_config()
        post_enabled = bool(post_cfg.get("enabled", False))
        post_tools: list[str] = list(post_cfg.get("tools", [])) if post_enabled else []
        enforce_failure: bool = bool(post_cfg.get("enforce_failure", action == "check"))

        # In JSON mode, we still need exit-code enforcement even if we skip
        # rendering post-check outputs. If a post-check tool is unavailable
        # and enforce_failure is enabled during check, append a failure result
        # so summaries and exit codes reflect the condition.
        if post_tools and json_output_mode and action == "check" and enforce_failure:
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

        if post_tools and not json_output_mode:
            # Print a clear post-checks section header
            logger.print_post_checks_header(action=action)

            for post_tool_name in post_tools:
                try:
                    tool_enum = ToolEnum[post_tool_name.upper()]
                except KeyError:
                    logger.warning(f"Unknown post-check tool: {post_tool_name}")
                    continue

                # If the tool isn't available in the current environment (e.g., unit
                # tests that stub a limited set of tools), skip without enforcing
                # failure. Post-checks are optional when the tool cannot be resolved
                # from the tool manager.
                try:
                    tool = tool_manager.get_tool(tool_enum)
                except Exception as e:
                    logger.warning(
                        f"Post-check '{post_tool_name}' unavailable: {e}",
                    )
                    continue
                tool_name = tool_enum.name.lower()

                # Post-checks run with explicit headers (reuse standard header)
                if not json_output_mode:
                    logger.print_tool_header(tool_name=tool_name, action=action)

                try:
                    # Load tool-specific config and common options
                    cfg: dict = load_lintro_tool_config(tool_name)
                    if cfg:
                        try:
                            tool.set_options(**cfg)
                        except Exception as e:
                            logger.debug(
                                f"Ignoring invalid config for {tool_name}: {e}",
                            )
                    tool.set_options(include_venv=include_venv)
                    if exclude:
                        exclude_patterns: list[str] = [
                            p.strip() for p in exclude.split(",")
                        ]
                        tool.set_options(exclude_patterns=exclude_patterns)

                    # For check: Black should run in check mode; for fmt: run fix
                    if action == "fmt" and tool.can_fix:
                        result = tool.fix(paths=paths)
                        issues_count = getattr(result, "issues_count", 0)
                        total_fixed += getattr(result, "fixed_issues_count", 0) or 0
                        total_remaining += (
                            getattr(result, "remaining_issues_count", issues_count) or 0
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
                            group_by=group_by_enum.value,
                            output_format=output_fmt_enum.value,
                            issues=issues,
                        )

                    if not json_output_mode:
                        logger.print_tool_result(
                            tool_name=tool_name,
                            output=(output if raw_output else formatted_output),
                            issues_count=issues_count,
                            raw_output_for_meta=output,
                            action=action,
                            success=getattr(result, "success", None),
                        )

                    all_results.append(result)
                except Exception as e:
                    # Do not crash the entire run due to missing optional post-check
                    # tool
                    logger.warning(f"Post-check '{post_tool_name}' failed: {e}")
                    # Only enforce failure when the tool was available and executed
                    if enforce_failure and action == "check":
                        from lintro.models.core.tool_result import ToolResult

                        all_results.append(
                            ToolResult(
                                name=post_tool_name,
                                success=False,
                                output=str(e),
                                issues_count=1,
                            ),
                        )

        # Handle output based on format
        if json_output_mode:
            # For JSON output, print JSON directly to stdout
            import datetime
            import json

            # Create a simple JSON structure with all results
            json_data = {
                "action": action,
                "timestamp": datetime.datetime.now().isoformat(),
                "tools": [result.name for result in all_results],
                "total_issues": sum(
                    getattr(result, "issues_count", 0) for result in all_results
                ),
                "total_fixed": (
                    sum((getattr(r, "fixed_issues_count", 0) or 0) for r in all_results)
                    if action == "fmt"
                    else None
                ),
                "total_remaining": (
                    sum(
                        (getattr(r, "remaining_issues_count", 0) or 0)
                        for r in all_results
                    )
                    if action == "fmt"
                    else None
                ),
                "results": [],
            }

            for result in all_results:
                result_data = {
                    "tool": result.name,
                    "success": getattr(result, "success", True),
                    "issues_count": getattr(result, "issues_count", 0),
                    "output": getattr(result, "output", ""),
                    "initial_issues_count": getattr(
                        result,
                        "initial_issues_count",
                        None,
                    ),
                    "fixed_issues_count": getattr(result, "fixed_issues_count", None),
                    "remaining_issues_count": getattr(
                        result,
                        "remaining_issues_count",
                        None,
                    ),
                }
                json_data["results"].append(result_data)

            print(json.dumps(json_data, indent=2))
        else:
            # Print rich execution summary with table and ASCII art
            logger.print_execution_summary(action=action, tool_results=all_results)

        # Save outputs
        try:
            output_manager.write_reports_from_results(results=all_results)
            logger.save_console_log()
            logger.debug("Saved all output files")
        except Exception as e:
            # Log at debug to avoid failing the run for non-critical persistence.
            logger.debug(f"Error saving outputs: {e}")

        # Return appropriate exit code
        if action == "fmt":
            # Format operations succeed if they complete successfully
            # (even if there are remaining unfixable issues)
            return DEFAULT_EXIT_CODE_SUCCESS
        else:  # check
            # Check operations fail if issues are found OR any tool reported failure
            any_failed: bool = any(
                not getattr(result, "success", True) for result in all_results
            )
            return (
                DEFAULT_EXIT_CODE_SUCCESS
                if (total_issues == 0 and not any_failed)
                else DEFAULT_EXIT_CODE_FAILURE
            )

    except Exception as e:
        logger.debug(f"Unexpected error: {e}")
        logger.save_console_log()
        return DEFAULT_EXIT_CODE_FAILURE
