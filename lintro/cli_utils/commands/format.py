"""Format command implementation using simplified Loguru-based approach."""

import click
from lintro.utils.simple_runner import run_lint_tools_simple


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
def format_code(
    paths: tuple[str, ...],
    tools: str | None,
    tool_options: str | None,
    exclude: str | None,
    include_venv: bool,
    group_by: str,
    output_format: str,
    verbose: bool,
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
    )

    # Exit with appropriate code
    if exit_code != 0:
        raise click.ClickException("Format found issues")
