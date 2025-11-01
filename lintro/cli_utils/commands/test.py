"""Test command implementation for running pytest tests."""

import click
from click.testing import CliRunner

from lintro.utils.tool_executor import run_lint_tools_simple

# Constants
DEFAULT_PATHS: list[str] = ["."]
DEFAULT_EXIT_CODE: int = 0
DEFAULT_ACTION: str = "test"


@click.command("test")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--exclude",
    type=str,
    help="Comma-separated list of patterns to exclude from testing",
)
@click.option(
    "--include-venv",
    is_flag=True,
    help="Include virtual environment directories in testing",
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
    "--verbose",
    is_flag=True,
    help="Show verbose output",
)
@click.option(
    "--raw-output",
    is_flag=True,
    help="Show raw tool output instead of formatted output",
)
@click.option(
    "--tool-options",
    type=str,
    help="Tool-specific options in the format option=value,option=value",
)
@click.option(
    "--enable-docker",
    is_flag=True,
    default=False,
    help="Enable Docker-specific tests",
)
def test_command(
    paths,
    exclude,
    include_venv,
    output,
    output_format,
    group_by,
    verbose,
    raw_output,
    tool_options,
    enable_docker,
) -> None:
    """Run tests using pytest.

    Args:
        paths: tuple: List of file/directory paths to test.
        exclude: str | None: Comma-separated patterns of files/dirs to exclude.
        include_venv: bool: Whether to include virtual environment directories.
        output: str | None: Path to output file for results.
        output_format: str: Format for displaying results (grid, json, etc).
        group_by: str: How to group issues in output (file, code, etc).
        verbose: bool: Whether to show verbose output during execution.
        raw_output: bool: Whether to show raw tool output instead of formatted output.
        tool_options: str | None: Tool-specific options.
        enable_docker: bool: Whether to enable Docker-specific tests.

    Raises:
        SystemExit: Process exit with the aggregated exit code.
    """
    # Add default paths if none provided
    if not paths:
        paths = DEFAULT_PATHS

    # Build tool options with pytest prefix
    tool_option_parts: list[str] = []

    # Add Docker enable option if flag is set
    if enable_docker:
        tool_option_parts.append("pt:run_docker_tests=True")

    if tool_options:
        # Prefix with "pt:" for pytest tool
        prefixed_options: list[str] = []
        for opt in tool_options.split(","):
            opt = opt.strip()
            if opt:
                if not opt.startswith("pt:"):
                    prefixed_options.append(f"pt:{opt}")
                else:
                    prefixed_options.append(opt)
        tool_option_parts.append(",".join(prefixed_options))

    combined_tool_options: str | None = (
        ",".join(tool_option_parts) if tool_option_parts else None
    )

    # Run with pytest tool
    exit_code: int = run_lint_tools_simple(
        action=DEFAULT_ACTION,
        paths=list(paths),
        tools="pt",
        tool_options=combined_tool_options,
        exclude=exclude,
        include_venv=include_venv,
        group_by=group_by,
        output_format=output_format,
        verbose=verbose,
        raw_output=raw_output,
    )

    # Exit with code only
    raise SystemExit(exit_code)


def test(
    paths,
    exclude,
    include_venv,
    output,
    output_format,
    group_by,
    verbose,
    tool_options,
) -> None:
    """Programmatic test function for backward compatibility.

    Args:
        paths: tuple: List of file/directory paths to test.
        exclude: str | None: Comma-separated patterns of files/dirs to exclude.
        include_venv: bool: Whether to include virtual environment directories.
        output: str | None: Path to output file for results.
        output_format: str: Format for displaying results.
        group_by: str: How to group issues in output.
        verbose: bool: Whether to show verbose output during execution.
        tool_options: str | None: Tool-specific options.

    Returns:
        None: This function does not return a value.
    """
    # Build arguments for the click command
    args: list[str] = []
    if paths:
        args.extend(paths)
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
    if verbose:
        args.append("--verbose")
    if tool_options:
        args.extend(["--tool-options", tool_options])

    runner = CliRunner()
    result = runner.invoke(test_command, args)

    if result.exit_code != DEFAULT_EXIT_CODE:
        import sys

        sys.exit(result.exit_code)
    return None
