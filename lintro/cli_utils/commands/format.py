"""Format command implementation using simplified Loguru-based approach."""

import click
from click.testing import CliRunner

from lintro.utils.tool_executor import run_lint_tools_simple

# Constants
DEFAULT_PATHS: list[str] = ["."]
DEFAULT_EXIT_CODE: int = 0
DEFAULT_ACTION: str = "fmt"


@click.command()
@click.pass_context
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--tools",
    default=None,
    help="Comma-separated list of tools to run (e.g., ruff,prettier) or 'all'.",
)
@click.option(
    "--tool-options",
    default=None,
    help="Tool-specific options in format tool:option=value,tool2:option=value.",
)
@click.option(
    "--exclude",
    default=None,
    help="Comma-separated patterns to exclude from formatting.",
)
@click.option(
    "--include-venv",
    is_flag=True,
    default=False,
    help="Include virtual environment directories in formatting.",
)
@click.option(
    "--group-by",
    default="auto",
    type=click.Choice(["file", "code", "none", "auto"]),
    help="How to group issues in output.",
)
@click.option(
    "--output-format",
    default="grid",
    type=click.Choice(["plain", "grid", "markdown", "html", "json", "csv"]),
    help="Output format for displaying results.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose output with debug information.",
)
@click.option(
    "--raw-output",
    is_flag=True,
    default=False,
    help="Show raw tool output instead of formatted output.",
)
def format_command(
    ctx: click.Context,
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
        ctx: click.Context: Click context object for command execution.
        paths: tuple[str, ...]:
            Paths to format (defaults to current directory if none provided).
        tools: str | None: Specific tools to run, or 'all' for all available tools.
        tool_options: str | None: Tool-specific configuration options.
        exclude: str | None: Patterns to exclude from formatting.
        include_venv: bool: Whether to include virtual environment directories.
        group_by: str: How to group issues in the output display.
        output_format: str: Format for displaying results.
        verbose: bool: Enable detailed debug output.
        raw_output: bool:
            Show raw tool output instead of formatted output.
    """
    # Default to current directory if no paths provided
    normalized_paths: list[str] = list(paths) if paths else list(DEFAULT_PATHS)

    # Run with simplified approach
    exit_code: int = run_lint_tools_simple(
        action=DEFAULT_ACTION,
        paths=normalized_paths,
        tools=tools,
        tool_options=tool_options,
        exclude=exclude,
        include_venv=include_venv,
        group_by=group_by,
        output_format=output_format,
        verbose=verbose,
        raw_output=raw_output,
    )

    # Exit with code from tool execution
    # For fmt action, exit_code is 1 only if there were execution errors
    # (not if issues were found and fixed - that's success)
    ctx.exit(exit_code)


def format_code(
    paths: list[str] | None = None,
    tools: str | None = None,
    tool_options: str | None = None,
    exclude: str | None = None,
    include_venv: bool = False,
    group_by: str = "auto",
    output_format: str = "grid",
    verbose: bool = False,
) -> None:
    """Programmatic format function.

    Args:
        paths: list[str] | None: List of file/directory paths to format.
        tools: str | None: Comma-separated list of tool names to run.
        tool_options: str | None: Tool-specific configuration options.
        exclude: str | None: Comma-separated patterns of files/dirs to exclude.
        include_venv: bool: Whether to include virtual environment directories.
        group_by: str: How to group issues in output (tool, file, etc).
        output_format: str: Format for displaying results (table, json, etc).
        verbose: bool: Whether to show verbose output during execution.

    Returns:
        None: This function does not return a value.

    Raises:
        RuntimeError: If format fails for any reason.
    """
    args: list[str] = []
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
    result = runner.invoke(format_command, args)
    if result.exit_code != DEFAULT_EXIT_CODE:
        raise RuntimeError(f"Format failed: {result.output}")
    return None


# Legacy alias for backward compatibility
format_code_legacy = format_code

# Export the Click command as the main interface
__all__ = ["format_command", "format_code", "format_code_legacy"]
