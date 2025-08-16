"""List tools command implementation for lintro CLI.

This module provides the core logic for the 'list_tools' command.
"""

import click

from lintro.enums.action import Action
from lintro.tools import tool_manager
from lintro.utils.console_logger import get_tool_emoji


@click.command("list-tools")
@click.option(
    "--output",
    type=click.Path(),
    help="Output file path for writing results",
)
@click.option(
    "--show-conflicts",
    is_flag=True,
    help="Show potential conflicts between tools",
)
def list_tools_command(
    output,
    show_conflicts,
) -> None:
    """List all available tools and their configurations.

    Args:
        output: Path to output file for writing results.
        show_conflicts: Whether to show potential conflicts between tools.
    """
    list_tools(output=output, show_conflicts=show_conflicts)


def list_tools(
    output: str | None,
    show_conflicts: bool,
) -> None:
    """List all available tools.

    Args:
        output: Output file path.
        show_conflicts: Whether to show potential conflicts between tools.
    """
    available_tools = tool_manager.get_available_tools()
    check_tools = tool_manager.get_check_tools()
    fix_tools = tool_manager.get_fix_tools()

    output_lines = []

    # Create header with emojis
    border = "=" * 70
    header_title = "🔧  Available Tools"
    emojis = "🔧 🔧 🔧 🔧 🔧"
    output_lines.append(f"{border}")
    output_lines.append(f"{header_title}    {emojis}")
    output_lines.append(f"{border}")
    output_lines.append("")

    for tool_enum, tool in available_tools.items():
        tool_name = tool_enum.name.lower()
        tool_description = getattr(tool.config, "description", tool.__class__.__name__)
        emoji = get_tool_emoji(tool_name)

        capabilities: list[str] = []
        if tool_enum in check_tools:
            capabilities.append(Action.CHECK.value)
        if tool_enum in fix_tools:
            capabilities.append(Action.FIX.value)

        output_lines.append(f"{emoji} {tool_name}: {tool_description}")
        output_lines.append(f"  Capabilities: {', '.join(capabilities)}")

        if (
            show_conflicts
            and hasattr(tool.config, "conflicts_with")
            and tool.config.conflicts_with
        ):
            conflicts = [
                conflict.name.lower()
                for conflict in tool.config.conflicts_with
                if conflict in available_tools
            ]
            if conflicts:
                output_lines.append(f"  Conflicts with: {', '.join(conflicts)}")

        output_lines.append("")

    # Add summary footer
    summary_border = "-" * 70
    output_lines.append(summary_border)
    output_lines.append(f"📊 Total tools: {len(available_tools)}")
    output_lines.append(f"🔍 Check tools: {len(check_tools)}")
    output_lines.append(f"🔧 Fix tools: {len(fix_tools)}")
    output_lines.append(summary_border)

    # Format output
    output_text = "\n".join(output_lines)

    # Print to console using click.echo for consistency
    click.echo(output_text)

    # Write to file if specified
    if output:
        try:
            with open(output, "w", encoding="utf-8") as f:
                f.write(output_text + "\n")
            success_msg = f"Output written to: {output}"
            click.echo(success_msg)
        except IOError as e:
            error_msg = f"Error writing to file {output}: {e}"
            click.echo(error_msg, err=True)
