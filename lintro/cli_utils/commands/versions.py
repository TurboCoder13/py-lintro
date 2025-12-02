"""Versions command for displaying tool version information."""

import click
from rich.console import Console
from rich.table import Table

from lintro.tools.core.version_requirements import get_all_tool_versions


@click.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed version information including install hints.",
)
def versions_command(verbose: bool) -> None:
    """Display version information for all supported tools.

    Shows each tool's current version, minimum required version, and status.
    Use --verbose to see installation hints for tools that don't meet requirements.
    """
    console = Console()
    tool_versions = get_all_tool_versions()

    table = Table(title="Tool Versions")
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Current", style="yellow")
    table.add_column("Minimum", style="green")
    table.add_column("Status", justify="center")

    if verbose:
        table.add_column("Install Hint", style="dim")

    # Sort tools by name for consistent output
    sorted_tools = sorted(tool_versions.items())

    for tool_name, version_info in sorted_tools:
        current = version_info.current_version or "unknown"
        minimum = version_info.min_version

        if version_info.version_check_passed:
            status = "[green]✓ PASS[/green]"
        elif version_info.error_message:
            status = "[red]✗ FAIL[/red]"
        else:
            status = "[yellow]? UNKNOWN[/yellow]"

        row = [tool_name, current, minimum, status]

        if verbose:
            hint = version_info.install_hint
            if (
                version_info.error_message
                and "Version" in version_info.error_message
                or version_info.error_message
            ):
                hint = f"{version_info.error_message}. {hint}"
            row.append(hint)

        table.add_row(*row)

    console.print(table)

    # Summary
    total_tools = len(tool_versions)
    passed_tools = sum(1 for v in tool_versions.values() if v.version_check_passed)
    failed_tools = total_tools - passed_tools

    if failed_tools > 0:
        console.print(
            f"\n[red]⚠️  {failed_tools} tool(s) do not meet "
            f"minimum version requirements.[/red]",
        )
        console.print(
            "[dim]Run with --verbose to see installation instructions.[/dim]",
        )
    else:
        console.print(
            f"\n[green]✅ All {total_tools} tools meet "
            f"minimum version requirements.[/green]",
        )
