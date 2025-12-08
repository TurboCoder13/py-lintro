"""List tools command implementation for lintro CLI.

This module provides the core logic for the 'list_tools' command.
"""

from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lintro.enums.action import Action
from lintro.tools import tool_manager
from lintro.tools.tool_enum import ToolEnum
from lintro.utils.console_logger import get_tool_emoji
from lintro.utils.unified_config import get_tool_priority, is_tool_injectable


def _resolve_conflicts(
    tool_config: Any,
    name_to_enum_map: dict[str, ToolEnum],
    available_tools: dict[ToolEnum, Any],
) -> list[str]:
    """Resolve conflict names for a tool.

    Args:
        tool_config: Tool configuration object.
        name_to_enum_map: Mapping of tool names to ToolEnum.
        available_tools: Dictionary of available tools.

    Returns:
        List of conflict tool names.
    """
    conflict_names: list[str] = []
    if hasattr(tool_config, "conflicts_with") and tool_config.conflicts_with:
        for conflict in tool_config.conflicts_with:
            conflict_enum: ToolEnum | None = None
            if isinstance(conflict, str):
                conflict_enum = name_to_enum_map.get(conflict.lower())
            elif isinstance(conflict, ToolEnum):
                conflict_enum = conflict
            if conflict_enum is not None and conflict_enum in available_tools:
                conflict_names.append(conflict_enum.name.lower())
    return conflict_names


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
    output: str | None,
    show_conflicts: bool,
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
    console = Console()
    available_tools = tool_manager.get_available_tools()
    check_tools = tool_manager.get_check_tools()
    fix_tools = tool_manager.get_fix_tools()

    # Header panel
    console.print(
        Panel.fit(
            "[bold cyan]🔧 Available Tools[/bold cyan]",
            border_style="cyan",
        ),
    )
    console.print()

    # Main tools table
    table = Table(title="Tool Details")
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Description", style="white", max_width=40)
    table.add_column("Capabilities", style="green")
    table.add_column("Priority", justify="center", style="yellow")
    table.add_column("Type", style="magenta")

    if show_conflicts:
        table.add_column("Conflicts", style="red")

    # Build name-to-enum map for conflict resolution
    name_to_enum_map = {t.name.lower(): t for t in ToolEnum}

    for tool_enum, tool in available_tools.items():
        tool_name = tool_enum.name.lower()
        tool_description = getattr(
            tool.config,
            "description",
            tool.__class__.__name__,
        )
        emoji = get_tool_emoji(tool_name)

        # Capabilities
        capabilities: list[str] = []
        if tool_enum in check_tools:
            capabilities.append("check")
        if tool_enum in fix_tools:
            capabilities.append("fix")
        caps_display = ", ".join(capabilities) if capabilities else "-"

        # Priority and type
        priority = get_tool_priority(tool_name)
        injectable = is_tool_injectable(tool_name)
        tool_type = "Syncable" if injectable else "Native only"

        row = [
            f"{emoji} {tool_name}",
            tool_description,
            caps_display,
            str(priority),
            tool_type,
        ]

        # Conflicts
        if show_conflicts:
            conflict_names = _resolve_conflicts(
                tool_config=tool.config,
                name_to_enum_map=name_to_enum_map,
                available_tools=available_tools,
            )
            row.append(", ".join(conflict_names) if conflict_names else "-")

        table.add_row(*row)

    console.print(table)
    console.print()

    # Summary table
    summary_table = Table(
        title="Summary",
        show_header=False,
        box=None,
    )
    summary_table.add_column("Metric", style="cyan", width=20)
    summary_table.add_column("Count", style="yellow", justify="right")

    summary_table.add_row("📊 Total tools", str(len(available_tools)))
    summary_table.add_row("🔍 Check tools", str(len(check_tools)))
    summary_table.add_row("🔧 Fix tools", str(len(fix_tools)))

    console.print(summary_table)

    # Write to file if specified
    if output:
        try:
            # For file output, use plain text format
            output_lines = _generate_plain_text_output(
                available_tools=available_tools,
                check_tools=check_tools,
                fix_tools=fix_tools,
                show_conflicts=show_conflicts,
            )
            with open(output, "w", encoding="utf-8") as f:
                f.write("\n".join(output_lines) + "\n")
            console.print()
            console.print(f"[green]✅ Output written to: {output}[/green]")
        except OSError as e:
            console.print(f"[red]Error writing to file {output}: {e}[/red]")


def _generate_plain_text_output(
    available_tools: dict[ToolEnum, Any],
    check_tools: dict[ToolEnum, Any],
    fix_tools: dict[ToolEnum, Any],
    show_conflicts: bool,
) -> list[str]:
    """Generate plain text output for file writing.

    Args:
        available_tools: Dictionary of available tools.
        check_tools: Dictionary of check-capable tools.
        fix_tools: Dictionary of fix-capable tools.
        show_conflicts: Whether to include conflict information.

    Returns:
        List of output lines.
    """
    output_lines: list[str] = []
    border = "=" * 70

    output_lines.append(border)
    output_lines.append("Available Tools")
    output_lines.append(border)
    output_lines.append("")

    name_to_enum_map = {t.name.lower(): t for t in ToolEnum}

    for tool_enum, tool in available_tools.items():
        tool_name = tool_enum.name.lower()
        tool_description = getattr(
            tool.config,
            "description",
            tool.__class__.__name__,
        )
        emoji = get_tool_emoji(tool_name)

        capabilities: list[str] = []
        if tool_enum in check_tools:
            capabilities.append(Action.CHECK.value)
        if tool_enum in fix_tools:
            capabilities.append(Action.FIX.value)

        capabilities_display = ", ".join(capabilities) if capabilities else "-"

        output_lines.append(f"{emoji} {tool_name}: {tool_description}")
        output_lines.append(f"  Capabilities: {capabilities_display}")

        if show_conflicts:
            conflict_names = _resolve_conflicts(
                tool_config=tool.config,
                name_to_enum_map=name_to_enum_map,
                available_tools=available_tools,
            )
            if conflict_names:
                output_lines.append(f"  Conflicts with: {', '.join(conflict_names)}")

        output_lines.append("")

    summary_border = "-" * 70
    output_lines.append(summary_border)
    output_lines.append(f"Total tools: {len(available_tools)}")
    output_lines.append(f"Check tools: {len(check_tools)}")
    output_lines.append(f"Fix tools: {len(fix_tools)}")
    output_lines.append(summary_border)

    return output_lines
