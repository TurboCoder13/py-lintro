"""Simplified runner for lintro commands.

Clean, straightforward approach using Loguru with rich formatting:
1. OutputManager - handles structured output files only
2. SimpleLintroLogger - handles console display AND logging with Loguru + rich formatting
3. No tee, no stream redirection, no complex state management
"""

from lintro.tools import tool_manager
from lintro.tools.tool_enum import ToolEnum
from lintro.utils.console_logger import create_logger
from lintro.utils.output_manager import OutputManager
from lintro.utils.tool_utils import format_tool_output


def _get_tools_to_run(tools: str | None, action: str) -> list[ToolEnum]:
    """Get the list of tools to run based on the tools string and action.

    Args:
        tools: Comma-separated tool names, "all", or None
        action: "check" or "fmt"

    Returns:
        List of ToolEnum instances to run

    Raises:
        ValueError: If unknown tool names are provided
    """
    if tools == "all" or tools is None:
        # Get all available tools for the action
        if action == "fmt":
            available_tools = tool_manager.get_fix_tools()
        else:  # check
            available_tools = tool_manager.get_check_tools()
        return list(available_tools.keys())

    # Parse specific tools
    tool_names = [name.strip().upper() for name in tools.split(",")]
    tools_to_run = []

    for name in tool_names:
        try:
            tool_enum = ToolEnum[name]
            # Verify the tool supports the requested action
            if action == "fmt":
                tool_instance = tool_manager.get_tool(tool_enum)
                if not tool_instance.can_fix:
                    raise ValueError(
                        f"Tool '{name.lower()}' does not support formatting"
                    )
            tools_to_run.append(tool_enum)
        except KeyError:
            available_names = [e.name.lower() for e in ToolEnum]
            raise ValueError(
                f"Unknown tool '{name.lower()}'. Available tools: {available_names}"
            )

    return tools_to_run


def _parse_tool_options(tool_options: str | None) -> dict[str, dict[str, str]]:
    """Parse tool options string into a dictionary.

    Args:
        tool_options: String in format "tool:option=value,tool2:option=value"

    Returns:
        Dictionary mapping tool names to their options
    """
    if not tool_options:
        return {}

    tool_option_dict = {}
    for opt in tool_options.split(","):
        if ":" in opt:
            tool_name, tool_opt = opt.split(":", 1)
            if "=" in tool_opt:
                opt_name, opt_value = tool_opt.split("=", 1)
                if tool_name not in tool_option_dict:
                    tool_option_dict[tool_name] = {}
                tool_option_dict[tool_name][opt_name] = opt_value

    return tool_option_dict


def run_lint_tools_simple(
    *,
    action: str,  # "check" or "fmt"
    paths: list[str],
    tools: str | None,
    tool_options: str | None,
    exclude: str | None,
    include_venv: bool,
    group_by: str,
    output_format: str,
    verbose: bool,
) -> int:
    """Simplified runner using Loguru-based logging with rich formatting.

    Clean approach with beautiful output:
    - SimpleLintroLogger handles ALL console output and file logging with rich formatting
    - OutputManager handles structured output files
    - No tee, no complex state management

    Args:
        action: "check" or "fmt"
        paths: List of paths to check
        tools: Comma-separated list of tools to run
        tool_options: Additional tool options
        exclude: Patterns to exclude
        include_venv: Whether to include virtual environments
        group_by: How to group results
        output_format: Output format for results
        verbose: Whether to enable verbose output

    Returns:
        Exit code (0 for success, 1 for failures)
    """
    # Initialize output manager for this run
    output_manager = OutputManager()
    run_dir = output_manager.run_dir

    # Create simplified logger with rich formatting
    logger = create_logger(run_dir=run_dir, verbose=verbose)

    logger.debug(f"Starting {action} command")
    logger.debug(f"Paths: {paths}")
    logger.debug(f"Tools: {tools}")
    logger.debug(f"Run directory: {run_dir}")

    try:
        # Get tools to run
        try:
            tools_to_run = _get_tools_to_run(tools, action)
        except ValueError as e:
            logger.error(str(e))
            logger.save_console_log()
            return 1

        if not tools_to_run:
            logger.warning("No tools found to run")
            logger.save_console_log()
            return 1

        # Parse tool options
        tool_option_dict = _parse_tool_options(tool_options)

        # Print main header
        tools_list = ", ".join(t.name.lower() for t in tools_to_run)
        logger.print_lintro_header(action, len(tools_to_run), tools_list)

        # Print verbose info if requested
        paths_list = ", ".join(paths)
        logger.print_verbose_info(action, tools_list, paths_list, output_format)

        all_results = []
        total_issues = 0

        # Run each tool with rich formatting
        for tool_enum in tools_to_run:
            tool = tool_manager.get_tool(tool_enum)
            tool_name = tool_enum.name.lower()

            # Print rich tool header
            logger.print_tool_header(tool_name, action)

            try:
                # Configure tool options
                if tool_name in tool_option_dict:
                    tool.set_options(**tool_option_dict[tool_name])

                # Set common options
                if exclude:
                    exclude_patterns = [
                        pattern.strip() for pattern in exclude.split(",")
                    ]
                    tool.set_options(exclude_patterns=exclude_patterns)

                tool.set_options(include_venv=include_venv)

                # Run the tool
                logger.debug(f"Executing {tool_name}")

                if action == "fmt":
                    result = tool.fix(paths=paths)
                else:  # check
                    result = tool.check(paths=paths)

                # Process result
                issues_count = getattr(result, "issues_count", 0)
                total_issues += issues_count

                # Format and display output
                output = getattr(result, "output", None)
                formatted_output = ""

                if output and output.strip():
                    formatted_output = format_tool_output(
                        tool_name=tool_name,
                        output=output,
                        group_by=group_by,
                        output_format=output_format,
                    )

                # Print tool results with rich formatting
                logger.print_tool_result(tool_name, formatted_output, issues_count)

                # Store result
                all_results.append(result)

                logger.debug(f"Completed {tool_name}: {issues_count} issues found")

            except Exception as e:
                logger.error(f"Error running {tool_name}: {e}")
                return 1

        # Print rich execution summary with table and ASCII art
        logger.print_execution_summary(action, all_results)

        # Save outputs
        try:
            output_manager.write_reports_from_results(all_results)
            logger.save_console_log()
            logger.debug("Saved all output files")
        except Exception as e:
            logger.error(f"Error saving outputs: {e}")

        # Return appropriate exit code
        if action == "fmt":
            # Format operations always succeed when they complete
            return 0
        else:  # check
            # Check operations fail if issues are found
            return 0 if total_issues == 0 else 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.save_console_log()
        return 1
