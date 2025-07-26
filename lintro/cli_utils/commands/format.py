"""Format command implementation using simplified Loguru-based approach."""

import click

from lintro.utils.tool_executor import run_lint_tools_simple


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--tools",
    default=None,
    help="Comma-separated list of tools to run (e.g., ruff,prettier) or 'all'",
)
@click.option(
    "--tool-options",
    default=None,
    help="Tool-specific options in format tool:option=value,tool2:option=value",
)
@click.option(
    "--exclude",
    default=None,
    help="Comma-separated patterns to exclude from formatting",
)
@click.option(
    "--include-venv",
    is_flag=True,
    default=False,
    help="Include virtual environment directories in formatting",
)
@click.option(
    "--group-by",
    default="auto",
    type=click.Choice(["file", "code", "none", "auto"]),
    help="How to group issues in output",
)
@click.option(
    "--output-format",
    default="grid",
    type=click.Choice(["plain", "grid", "markdown", "html", "json", "csv"]),
    help="Output format for displaying results",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose output with debug information",
)
@click.option(
    "--raw-output",
    is_flag=True,
    default=False,
    help="Show raw tool output instead of formatted output",
)
def format_code(
    paths: tuple[str, ...],
    tools: str | None,
    tool_options: str | None,
    exclude: str | None,
    include_venv: bool,
    group_by: str,
    output_format: str,
    verbose: bool,
    raw_output: bool,
) -> None:
    """Format code using configured formatting tools.

    Runs code formatting tools on the specified paths to automatically fix style issues.
    Uses simplified Loguru-based logging for clean output and proper file logging.

    Args:
        paths: Paths to format (defaults to current directory if none provided)
        tools: Specific tools to run, or 'all' for all available tools
        tool_options: Tool-specific configuration options
        exclude: Patterns to exclude from formatting
        include_venv: Whether to include virtual environment directories
        group_by: How to group issues in the output display
        output_format: Format for displaying results
        verbose: Enable detailed debug output
        raw_output: Show raw tool output instead of formatted output

    Raises:
        ClickException: If issues are found during formatting.
    """
    # Default to current directory if no paths provided
    if not paths:
        paths = ["."]

    # Run with simplified approach
    exit_code = run_lint_tools_simple(
        action="fmt",
        paths=list(paths),
        tools=tools,
        tool_options=tool_options,
        exclude=exclude,
        include_venv=include_venv,
        group_by=group_by,
        output_format=output_format,
        verbose=verbose,
        raw_output=raw_output,
    )

    # Exit with appropriate code
    if exit_code != 0:
        raise click.ClickException("Format found issues")


def format_code_legacy(
    paths: list[str] | None = None,
    tools: str | None = None,
    tool_options: str | None = None,
    exclude: str | None = None,
    include_venv: bool = False,
    group_by: str = "auto",
    output_format: str = "grid",
    verbose: bool = False,
) -> None:
    """Legacy format function for backward compatibility.

    Args:
        paths: List of file/directory paths to format.
        tools: Comma-separated list of tool names to run.
        tool_options: Tool-specific configuration options.
        exclude: Comma-separated patterns of files/dirs to exclude.
        include_venv: Whether to include virtual environment directories.
        group_by: How to group issues in output (tool, file, etc).
        output_format: Format for displaying results (table, json, etc).
        verbose: Whether to show verbose output during execution.

    Returns:
        None: This function does not return a value.

    Raises:
        Exception: If format fails for any reason.
    """
    from click.testing import CliRunner

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
    if group_by:
        args.extend(["--group-by", group_by])
    if output_format:
        args.extend(["--output-format", output_format])
    if verbose:
        args.append("--verbose")

    runner = CliRunner()
    result = runner.invoke(format_code, args)
    if result.exit_code != 0:
        raise Exception(f"Format failed: {result.output}")
    return None
