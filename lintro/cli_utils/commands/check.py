"""Check command implementation for lintro CLI.

This module provides the core logic for the 'check' command.
"""

from lintro.models.core.tool_result import ToolResult
from lintro.tools import tool_manager
from lintro.utils.formatting import print_summary, print_tool_footer, print_tool_header
from lintro.utils.tool_utils import format_tool_output
from lintro.utils.logging_utils import get_logger
from lintro.utils.output_manager import OutputManager
import sys
import click


@click.command("check")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--tools",
    type=str,
    help='Comma-separated list of tools to run. Use "all" to run all available tools.',
)
@click.option(
    "--tool-options",
    type=str,
    help="Tool-specific options in the format tool:option=value,tool:option=value",
)
@click.option(
    "--exclude",
    type=str,
    help="Comma-separated list of patterns to exclude from processing",
)
@click.option(
    "--include-venv",
    is_flag=True,
    help="Include virtual environment directories in processing",
)
@click.option(
    "--group-by",
    type=click.Choice(["file", "code", "none", "auto"]),
    default="file",
    help="How to group issues in the output",
)
@click.option(
    "--ignore-conflicts",
    is_flag=True,
    help="Ignore potential conflicts between tools",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show verbose output",
)
@click.option(
    "--no-log",
    is_flag=True,
    help="Disable logging to file",
)
def check_command(
    paths,
    tools,
    tool_options,
    exclude,
    include_venv,
    group_by,
    ignore_conflicts,
    verbose,
    no_log,
):
    """Check files for issues using the specified tools."""
    if not paths:
        paths = ["."]
    check(
        paths=paths,
        tools=tools,
        tool_options=tool_options,
        exclude=exclude,
        include_venv=include_venv,
        group_by=group_by,
        ignore_conflicts=ignore_conflicts,
        verbose=verbose,
        no_log=no_log,
    )


def check(
    paths,
    tools,
    tool_options,
    exclude,
    include_venv,
    group_by,
    ignore_conflicts,
    verbose,
    no_log,
):
    """Check files for issues using the specified tools."""
    logger = get_logger(verbose=verbose) if not no_log else None
    if not paths:
        paths = ["."]
    # Build a list of tool-specific options
    tool_option_dict = {}
    if tool_options:
        for opt in tool_options.split(","):
            if ":" in opt:
                tool_name, tool_opt = opt.split(":", 1)
                if "=" in tool_opt:
                    opt_name, opt_value = tool_opt.split("=", 1)
                    if tool_name not in tool_option_dict:
                        tool_option_dict[tool_name] = {}
                    tool_option_dict[tool_name][opt_name] = opt_value
    # Parse tools to run
    if tools == "all":
        available_tools = tool_manager.get_check_tools()
        tools_to_run = list(available_tools.keys())
    elif tools:
        from lintro.tools.tool_enum import ToolEnum
        tool_names = [name.strip().upper() for name in tools.split(",")]
        tools_to_run = []
        for name in tool_names:
            try:
                tool_enum = ToolEnum[name]
                tools_to_run.append(tool_enum)
            except KeyError:
                error_msg = f"Warning: Unknown tool '{name}'. Available tools: {[e.name.lower() for e in ToolEnum]}"
                click.echo(error_msg, err=True)
                if logger:
                    logger.warning(error_msg)
    else:
        tools_to_run = list(tool_manager.get_check_tools().keys())
    if not tools_to_run:
        error_msg = "No tools to run. Use --tools to specify tools or --help for more information."
        click.echo(error_msg, err=True)
        return
    tools_to_run = tool_manager.get_tool_execution_order(tools_to_run, ignore_conflicts)
    # Output manager integration
    output_manager = OutputManager()
    output_manager.cleanup_old_runs()
    run_dir = output_manager.get_run_dir()
    click.echo(f"[LINTRO] All output formats will be auto-generated in {run_dir}")
    # Capture console output for logging
    console_log = []
    all_results = []
    for tool_enum in tools_to_run:
        tool = tool_manager.get_tool(tool_enum)
        tool_name = tool_enum.name.lower()
        console_log.append(f"Running {tool_name}...")
        tool_results = []
        issues_count = 0
        try:
            if hasattr(tool, "check"):
                for path in paths:
                    result = tool.check([path])
                    if result:
                        tool_results.append(result)
                        if hasattr(result, "issues_count"):
                            issues_count += result.issues_count
                        elif hasattr(result, "issues") and result.issues:
                            issues_count += len(result.issues)
        except Exception as e:
            error_msg = f"Error running {tool_name}: {e}"
            console_log.append(error_msg)
            if logger:
                logger.error(error_msg)
        # Print tool output to console and log
        tool_output = ""
        for result in tool_results:
            if hasattr(result, "output") and result.output:
                tool_output += result.output + "\n"
            elif hasattr(result, "issues"):
                for issue in result.issues:
                    tool_output += str(issue) + "\n"
        if tool_output.strip():
            console_log.append(tool_output.strip())
        all_results.extend(tool_results)
    # Write console log
    output_manager.write_console_log("\n".join(console_log))
    # Write results.json (keep as before)
    output_manager.write_json([r.__dict__ for r in all_results], filename="results.json")
    # Write all reports (markdown, html, csv)
    output_manager.write_reports_from_results(all_results)
    click.echo(f"[LINTRO] Results written to {run_dir}")

    # Generate and output structured format to file (or stdout if no file for structured formats)
    # This block is now handled by the OutputManager for all formats.
    # If you want to keep the old structured output logic, you'd need to re-implement it here
    # based on the all_results collected by the OutputManager.
    # For now, we'll just print a message indicating the new behavior.
    click.echo("[LINTRO] All output formats have been written to the run directory.")

    # Show summary table for console output (like old style)
    if not is_structured_format:
        click.echo()  # Add spacing
        print_summary(
            results=all_results,
            action="check",
            file=None,
            output_format="grid",  # Use grid for nice table format
        )

    # Exit with appropriate code based on whether issues were found
    total_issues = sum(result.issues_count for result in all_results)
    if total_issues > 0:
        if logger:
            logger.info(
                f"Check completed with {total_issues} total issues - exiting with code 1"
            )
        sys.exit(1)
    else:
        if logger:
            logger.info(
                "Check completed successfully with no issues - exiting with code 0"
            )
