"""Check command implementation for lintro CLI.

This module provides the core logic for the 'check' command.

Functions:
    check_command: CLI command for checking files with various tools.
    check: Legacy function for backward compatibility.
"""

import click

from lintro.utils.tool_executor import run_lint_tools_simple


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
    "--output",
    type=click.Path(),
    help="Output file path for writing results",
)
@click.option(
    "--output-format",
    type=click.Choice(["plain", "grid", "markdown", "html", "json", "csv"]),
    default="grid",
    help="Output format for displaying results",
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
@click.option(
    "--raw-output",
    is_flag=True,
    help="Show raw tool output instead of formatted output",
)
def check_command(
    paths,
    tools,
    tool_options,
    exclude,
    include_venv,
    output,
    output_format,
    group_by,
    ignore_conflicts,
    verbose,
    no_log,
    raw_output,
):
    """Check files for issues using the specified tools.

    Args:
        paths: List of file/directory paths to check.
        tools: Comma-separated list of tool names to run.
        tool_options: Tool-specific configuration options.
        exclude: Comma-separated patterns of files/dirs to exclude.
        include_venv: Whether to include virtual environment directories.
        output: Path to output file for results.
        output_format: Format for displaying results (table, json, etc).
        group_by: How to group issues in output (tool, file, etc).
        ignore_conflicts: Whether to ignore tool configuration conflicts.
        verbose: Whether to show verbose output during execution.
        no_log: Whether to disable logging to file.
        raw_output: Whether to show raw tool output instead of formatted output.

    Returns:
        None: This function does not return a value.

    Raises:
        ClickException: If issues are found during checking.
    """
    # Add default paths if none provided
    if not paths:
        paths = ["."]

    # Build tool-specific options string
    tool_option_parts = []
    if tool_options:
        tool_option_parts.append(tool_options)

    # Removed darglint_timeout and prettier_timeout handling
    combined_tool_options = ",".join(tool_option_parts) if tool_option_parts else None

    # Run with simplified approach
    exit_code = run_lint_tools_simple(
        action="check",
        paths=list(paths),
        tools=tools,
        tool_options=combined_tool_options,
        exclude=exclude,
        include_venv=include_venv,
        group_by=group_by,
        output_format=output_format,
        verbose=verbose,
        raw_output=raw_output,
    )

    # Exit with appropriate code
    if exit_code != 0:
        raise click.ClickException("Check found issues")
    return None


def check(
    paths,
    tools,
    tool_options,
    exclude,
    include_venv,
    output,
    output_format,
    group_by,
    ignore_conflicts,
    verbose,
    no_log,
):
    """Legacy check function for backward compatibility.

    Args:
        paths: List of file/directory paths to check.
        tools: Comma-separated list of tool names to run.
        tool_options: Tool-specific configuration options.
        exclude: Comma-separated patterns of files/dirs to exclude.
        include_venv: Whether to include virtual environment directories.
        output: Path to output file for results.
        output_format: Format for displaying results (table, json, etc).
        group_by: How to group issues in output (tool, file, etc).
        ignore_conflicts: Whether to ignore tool configuration conflicts.
        verbose: Whether to show verbose output during execution.
        no_log: Whether to disable logging to file.

    Returns:
        None: This function does not return a value.
    """
    import sys

    from click.testing import CliRunner

    # Build arguments for the click command
    args = []
    if paths:
        args.extend(paths)
    if tools:
        args.extend(["--tools", tools])
    if tool_options:
        args.extend(["--tool-options", tool_options])
    if exclude:
        args.extend(["--exclude", exclude])
    if include_venv:
        args.append("--include-venv")
    if output:
        args.extend(["--output", output])
    if output_format:
        args.extend(["--output-format", output_format])
    if group_by:
        args.extend(["--group-by", group_by])
    if ignore_conflicts:
        args.append("--ignore-conflicts")
    # Removed darglint_timeout and prettier_timeout handling
    if verbose:
        args.append("--verbose")
    if no_log:
        args.append("--no-log")

    runner = CliRunner()
    result = runner.invoke(check_command, args)

    if result.exit_code != 0:
        sys.exit(result.exit_code)
    return None
