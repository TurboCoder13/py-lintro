"""Fmt command implementation for lintro CLI.

This module provides the core logic for the 'fmt' command.
"""

from lintro.models.core.tool_result import ToolResult
from lintro.tools import tool_manager
from lintro.utils.formatting import print_summary, print_tool_footer, print_tool_header
from lintro.utils.tool_utils import format_tool_output
from lintro.utils.logging_utils import get_logger
import sys
import click


@click.command("fmt")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--tools",
    type=str,
    help='Comma-separated list of tools to run. Use "all" to run all available tools.',
)
@click.option(
    "--all",
    "use_all_tools",
    is_flag=True,
    help="Run all available formatting tools.",
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
    "--output",
    type=click.Path(),
    help="Output file path for writing results",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["plain", "grid", "markdown", "html", "json", "csv"]),
    default="grid",
    help="Output format for displaying results",
)
@click.option(
    "--group-by",
    type=click.Choice(["file", "code", "none", "auto"]),
    default="auto",
    help="How to group issues in the output",
)
@click.option(
    "--ignore-conflicts",
    is_flag=True,
    help="Ignore potential conflicts between tools",
)
@click.option(
    "--darglint-timeout",
    type=int,
    help="Timeout for darglint in seconds",
)
@click.option(
    "--prettier-timeout",
    type=int,
    help="Timeout for prettier in seconds",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show verbose output",
)
@click.option(
    "--debug-file",
    type=click.Path(),
    help="Path to debug file",
)
def fmt_command(
    paths,
    tools,
    use_all_tools,
    tool_options,
    exclude,
    include_venv,
    output,
    output_format,
    group_by,
    ignore_conflicts,
    darglint_timeout,
    prettier_timeout,
    verbose,
    debug_file,
):
    """Fix (format) files using the specified tools.

    This command will auto-discover all files for each tool based on their file patterns
    and apply formatting fixes. It respects .lintro-ignore rules and processes the entire
    repository by default.

    Args:
        paths: List of file/directory paths to format (defaults to current directory).
        tools: Comma-separated list of tool names to run.
        use_all_tools: Whether to run all available tools.
        tool_options: Tool-specific configuration options.
        exclude: Comma-separated patterns of files/dirs to exclude.
        include_venv: Whether to include virtual environment directories.
        output: Path to output file for results.
        output_format: Format for displaying results (table, json, etc).
        group_by: How to group issues in output (tool, file, etc).
        ignore_conflicts: Whether to ignore tool configuration conflicts.
        darglint_timeout: Timeout in seconds for darglint tool.
        prettier_timeout: Timeout in seconds for prettier tool.
        verbose: Whether to show verbose output during execution.
        debug_file: Path to debug log file.
    """
    # Add default paths if none provided
    if not paths:
        paths = ["."]

    # Set tools to "all" if --all flag is used
    if use_all_tools:
        tools = "all"

    fmt(
        paths=paths,
        tools=tools,
        tool_options=tool_options,
        exclude=exclude,
        include_venv=include_venv,
        output=output,
        output_format=output_format,
        group_by=group_by,
        ignore_conflicts=ignore_conflicts,
        darglint_timeout=darglint_timeout,
        prettier_timeout=prettier_timeout,
        verbose=verbose,
        debug_file=debug_file,
    )


def fmt(
    paths: list[str],
    tools: str | None,
    tool_options: str | None,
    exclude: str | None,
    include_venv: bool,
    output: str | None,
    output_format: str,
    group_by: str,
    ignore_conflicts: bool,
    darglint_timeout: int | None,
    prettier_timeout: int | None,
    verbose: bool = False,
    debug_file: str | None = None,
) -> None:
    """Format files using the specified tools.

    This function auto-discovers all files for each tool based on their file patterns
    and applies formatting fixes. It respects .lintro-ignore rules.

    Args:
        paths: List of paths to format.
        tools: Comma-separated list of tools to run.
        tool_options: Tool-specific options.
        exclude: Comma-separated patterns to exclude.
        include_venv: Whether to include virtual environment directories.
        output: Output file path.
        output_format: Output format for displaying results.
        group_by: How to group issues in the output.
        ignore_conflicts: Whether to ignore tool conflicts.
        darglint_timeout: Timeout for darglint.
        prettier_timeout: Timeout for prettier.
        verbose: Show verbose output.
        debug_file: Path to debug file.
    """
    logger = get_logger()

    # Parse and validate exclude patterns
    exclude_patterns = []
    if exclude:
        exclude_patterns = [pattern.strip() for pattern in exclude.split(",")]
        logger.debug(f"Exclude patterns parsed: {exclude_patterns}")

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

    # Override with specific timeout options if provided
    if darglint_timeout is not None:
        if "darglint" not in tool_option_dict:
            tool_option_dict["darglint"] = {}
        tool_option_dict["darglint"]["timeout"] = darglint_timeout

    if prettier_timeout is not None:
        if "prettier" not in tool_option_dict:
            tool_option_dict["prettier"] = {}
        tool_option_dict["prettier"]["timeout"] = prettier_timeout

    # Parse tools to run
    if tools == "all":
        available_tools = tool_manager.get_fix_tools()
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
        tools_to_run = list(tool_manager.get_fix_tools().keys())

    if not tools_to_run:
        error_msg = "No tools to run. Use --tools to specify tools or --help for more information."
        click.echo(error_msg, err=True)
        return

    # Get execution order (handles conflicts)
    tools_to_run = tool_manager.get_tool_execution_order(tools_to_run, ignore_conflicts)

    # Determine if we're using a structured format that should go to file
    structured_formats = ["json", "markdown", "html", "csv"]
    is_structured_format = output_format in structured_formats
    console_format = "grid"  # Always use grid for console display

    if verbose or not is_structured_format:
        # Create consistent header for run information
        info_border = "=" * 70
        info_title = "🔧  Format Configuration"
        info_emojis = "🔧 🔧 🔧 🔧 🔧"
        info_header = f"{info_border}\n{info_title}    {info_emojis}\n{info_border}\n"
        click.echo(info_header)

        tools_list = ", ".join([tool.name.lower() for tool in tools_to_run])
        paths_list = ", ".join(list(paths))

        click.echo(f"🔧 Running tools: {tools_list}")
        click.echo(f"📁 Formatting paths: {paths_list}")
        click.echo("🔍 Auto-discovering files for each tool (respects .lintro-ignore)")
        if is_structured_format:
            click.echo(
                f"📊 Output format: {output_format} → {'file' if output else 'stdout'}"
            )
            click.echo(f"📺 Console format: {console_format}")
        else:
            click.echo(f"📊 Output format: {output_format}")
        click.echo()

        if logger:
            logger.info(
                f"Running tools: {[tool.name.lower() for tool in tools_to_run]}"
            )
            logger.info(f"Formatting paths: {list(paths)}")
            logger.info(f"Output format: {output_format}")

    all_results = []
    output_file = None

    # Open output file if specified
    if output:
        try:
            output_file = open(output, "w", encoding="utf-8")
        except IOError as e:
            error_msg = f"Error opening output file {output}: {e}"
            click.echo(error_msg, err=True, file=sys.stderr)
            if logger:
                logger.error(error_msg)
            return

    try:
        # Run each tool
        for tool_enum in tools_to_run:
            tool = tool_manager.get_tool(tool_enum)
            tool_name = tool_enum.name.lower()

            # Set tool-specific options if provided
            if tool_name in tool_option_dict:
                tool.set_options(**tool_option_dict[tool_name])

            # Set common options
            tool.set_options(
                exclude_patterns=exclude_patterns,
                include_venv=include_venv,
            )

            # Print tool header (only for console formats)
            print_tool_header(
                tool_name=tool_name,
                action="fmt",
                file=None,
                output_format=console_format,
            )

            tool_results = []
            issues_count = 0

            try:
                # Check if tool has fix method for formatting
                if hasattr(tool, "fix"):
                    if verbose:
                        tool_msg = f"  Running {tool_name} on auto-discovered files"
                        click.echo(tool_msg)
                        if logger:
                            logger.debug(tool_msg)

                    # Run the tool's fix method - it will auto-discover files using walk_files_with_excludes
                    result = tool.fix(paths)
                    if result:
                        tool_results.append(result)
                        if hasattr(result, "issues_count"):
                            issues_count += result.issues_count
                        elif hasattr(result, "issues") and result.issues:
                            issues_count += len(result.issues)
                else:
                    warning_msg = f"Warning: {tool_name} does not support formatting"
                    click.echo(warning_msg, err=True)
                    if logger:
                        logger.warning(warning_msg)

            except Exception as e:
                error_msg = f"Error running {tool_name}: {e}"
                click.echo(error_msg, err=True)
                if logger:
                    logger.error(error_msg)
                if verbose:
                    import traceback

                    traceback.print_exc()

            # For console display (non-structured formats), show formatted table output
            if tool_results and not is_structured_format:
                # Get the raw output from results
                tool_output = ""
                for result in tool_results:
                    if hasattr(result, "output") and result.output:
                        tool_output += result.output + "\n"
                    elif hasattr(result, "issues"):
                        # Fallback: create simple output from issues
                        for issue in result.issues:
                            tool_output += str(issue) + "\n"

                # Display tool output if there's meaningful content
                if tool_output.strip() and tool_output.strip() != "No issues found.":
                    # For fmt command, display raw output if it's human-readable
                    # (not JSON that needs parsing)
                    if tool_output.strip().startswith("[") and tool_name in [
                        "ruff",
                        "darglint",
                        "prettier",
                    ]:
                        # JSON output - use tool-specific formatters
                        formatted_output = format_tool_output(
                            tool_name=tool_name,
                            output=tool_output,
                            group_by=group_by,
                            output_format=console_format,  # Use console format (grid)
                        )
                        click.echo(formatted_output)
                    else:
                        # Human-readable output - display directly
                        click.echo(tool_output.strip())

            # Print tool footer (only for console)
            # For fmt command, use the actual success from the tool result
            tool_success = True
            if tool_results:
                tool_success = (
                    tool_results[0].success
                    if hasattr(tool_results[0], "success")
                    else True
                )

            # Get the raw output from results for footer logic
            tool_output = ""
            for result in tool_results:
                if hasattr(result, "output") and result.output:
                    tool_output += result.output + "\n"
                elif hasattr(result, "issues"):
                    # Fallback: create simple output from issues
                    for issue in result.issues:
                        tool_output += str(issue) + "\n"

            print_tool_footer(
                success=tool_success,
                issues_count=issues_count,
                file=None,
                output_format=console_format,
                tool_name=tool_name,
                tool_output=tool_output,
                action="fmt",
            )

            # Add results to overall results - generate both console and structured output
            if tool_results:
                # Get raw output for processing
                tool_output = ""
                for result in tool_results:
                    if hasattr(result, "output") and result.output:
                        tool_output += result.output + "\n"
                    elif hasattr(result, "issues"):
                        # Fallback: create simple output from issues
                        for issue in result.issues:
                            tool_output += str(issue) + "\n"

                # Generate structured output for file
                structured_output = ""
                if tool_output.strip():
                    structured_output = format_tool_output(
                        tool_name=tool_name,
                        output=tool_output,
                        group_by=group_by,
                        output_format=output_format,
                    )

                # Aggregate results per tool
                tool_result = ToolResult(
                    name=tool_name,
                    success=tool_results[0].success if tool_results else True,
                    output=getattr(tool_results[0], "output", "")
                    if tool_results
                    else "",
                    issues_count=issues_count,
                    formatted_output=structured_output,
                )
                all_results.append(tool_result)
            else:
                # Create a result even if no tool results (tool ran but found nothing)
                no_issues_output = format_tool_output(
                    tool_name=tool_name,
                    output="",
                    group_by=group_by,
                    output_format=output_format,
                )

                tool_result = ToolResult(
                    name=tool_name,
                    success=True,
                    output="No issues found.",
                    issues_count=0,
                    formatted_output=no_issues_output,
                )
                all_results.append(tool_result)

        # Generate and output structured format to file (or stdout if no file for structured formats)
        if is_structured_format:
            print_summary(
                results=all_results,
                action="fmt",
                file=output_file if output_file else None,
                output_format=output_format,
            )

            if output_file:
                success_msg = f"✅ {output_format.upper()} results written to: {output}"
                click.echo(success_msg)
                if logger:
                    logger.info(success_msg)
            elif output_format == "json":
                # For JSON to stdout, we already printed it, so just add a note
                pass

        # Old style: no summary table for console output, just ASCII art
        if not is_structured_format:
            print_summary(
                results=all_results,
                action="fmt",
                file=None,
                output_format="plain",  # Use plain to get just ASCII art
            )

    finally:
        # Close output file if it was opened
        if output_file:
            try:
                output_file.close()
            except IOError as e:
                error_msg = f"Error closing output file {output}: {e}"
                click.echo(error_msg, err=True, file=sys.stderr)
                if logger:
                    logger.error(error_msg)
