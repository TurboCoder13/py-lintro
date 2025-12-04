"""Config command for displaying Lintro configuration status."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lintro.utils.unified_config import (
    UnifiedConfigManager,
    get_effective_line_length,
    get_ordered_tools,
    get_tool_order_config,
    get_tool_priority,
    is_tool_injectable,
    validate_config_consistency,
)


@click.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed configuration including native tool configs.",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output configuration as JSON.",
)
def config_command(
    verbose: bool,
    json_output: bool,
) -> None:
    """Display Lintro configuration status.

    Shows the unified configuration for all tools including:
    - Global settings (line_length, tool ordering strategy)
    - Tool execution order based on configured strategy
    - Per-tool effective configuration
    - Configuration warnings and inconsistencies

    Args:
        verbose: Show detailed configuration including native tool configs.
        json_output: Output configuration as JSON.
    """
    console = Console()
    config_manager = UnifiedConfigManager()

    if json_output:
        _output_json(config_manager=config_manager)
        return

    _output_rich(
        console=console,
        config_manager=config_manager,
        verbose=verbose,
    )


def _output_json(config_manager: UnifiedConfigManager) -> None:
    """Output configuration as JSON.

    Args:
        config_manager: UnifiedConfigManager instance
    """
    import json

    order_config = get_tool_order_config()
    tool_names = list(config_manager.tool_configs.keys())
    ordered_tools = get_ordered_tools(tool_names)

    output = {
        "global_settings": {
            "line_length": get_effective_line_length("ruff"),
            "tool_order": order_config.get("strategy", "priority"),
            "custom_order": order_config.get("custom_order", []),
            "priority_overrides": order_config.get("priority_overrides", {}),
        },
        "tool_execution_order": [
            {"tool": t, "priority": get_tool_priority(t)} for t in ordered_tools
        ],
        "tool_configs": {},
        "warnings": validate_config_consistency(),
    }

    for tool_name, info in config_manager.tool_configs.items():
        output["tool_configs"][tool_name] = {
            "is_injectable": info.is_injectable,
            "effective_line_length": info.effective_config.get("line_length"),
            "lintro_config": info.lintro_tool_config,
            "native_config": info.native_config if info.native_config else None,
            "warnings": info.warnings,
        }

    print(json.dumps(output, indent=2))


def _output_rich(
    console: Console,
    config_manager: UnifiedConfigManager,
    verbose: bool,
) -> None:
    """Output configuration using Rich formatting.

    Args:
        console: Rich Console instance
        config_manager: UnifiedConfigManager instance
        verbose: Whether to show verbose output
    """
    order_config = get_tool_order_config()
    central_line_length = get_effective_line_length("ruff")

    # Header panel
    console.print(
        Panel.fit(
            "[bold cyan]Lintro Configuration Report[/bold cyan]",
            border_style="cyan",
        ),
    )
    console.print()

    # Global Settings Section
    global_table = Table(
        title="Global Settings",
        show_header=False,
        box=None,
    )
    global_table.add_column("Setting", style="cyan", width=25)
    global_table.add_column("Value", style="yellow")

    global_table.add_row(
        "Central line_length",
        (
            str(central_line_length)
            if central_line_length
            else "[dim]Not configured[/dim]"
        ),
    )
    global_table.add_row(
        "Tool order strategy",
        order_config.get("strategy", "priority"),
    )

    if order_config.get("custom_order"):
        global_table.add_row(
            "Custom order",
            ", ".join(order_config["custom_order"]),
        )

    if order_config.get("priority_overrides"):
        overrides_str = ", ".join(
            f"{k}={v}" for k, v in order_config["priority_overrides"].items()
        )
        global_table.add_row("Priority overrides", overrides_str)

    console.print(global_table)
    console.print()

    # Tool Execution Order Section
    tool_names = list(config_manager.tool_configs.keys())
    ordered_tools = get_ordered_tools(tool_names)

    order_table = Table(title="Tool Execution Order")
    order_table.add_column("#", style="dim", justify="right", width=3)
    order_table.add_column("Tool", style="cyan")
    order_table.add_column("Priority", justify="center", style="yellow")
    order_table.add_column("Type", style="green")

    for idx, tool_name in enumerate(ordered_tools, 1):
        priority = get_tool_priority(tool_name)
        injectable = is_tool_injectable(tool_name)
        tool_type = "Syncable" if injectable else "Native only"

        order_table.add_row(
            str(idx),
            tool_name,
            str(priority),
            tool_type,
        )

    console.print(order_table)
    console.print()

    # Per-Tool Configuration Section
    config_table = Table(title="Per-Tool Configuration")
    config_table.add_column("Tool", style="cyan")
    config_table.add_column("Sync Status", justify="center")
    config_table.add_column("Line Length", justify="center", style="yellow")
    config_table.add_column("Lintro Config", style="dim")

    if verbose:
        config_table.add_column("Native Config", style="dim")

    for tool_name, info in config_manager.tool_configs.items():
        status = (
            "[green]✓ Syncable[/green]"
            if info.is_injectable
            else "[yellow]⚠ Native only[/yellow]"
        )
        effective_ll = info.effective_config.get("line_length")
        ll_display = str(effective_ll) if effective_ll else "[dim]default[/dim]"

        lintro_cfg = (
            str(info.lintro_tool_config)
            if info.lintro_tool_config
            else "[dim]None[/dim]"
        )

        row = [tool_name, status, ll_display, lintro_cfg]

        if verbose:
            native_cfg = (
                str(info.native_config) if info.native_config else "[dim]None[/dim]"
            )
            row.append(native_cfg)

        config_table.add_row(*row)

    console.print(config_table)
    console.print()

    # Warnings Section
    warnings = validate_config_consistency()
    if warnings:
        console.print("[bold red]Configuration Warnings[/bold red]")
        for warning in warnings:
            console.print(f"  [yellow]⚠️[/yellow]  {warning}")
        console.print()
        console.print(
            "[dim]Tools marked 'Native only' cannot be configured by Lintro. "
            "Update their config files manually for consistency.[/dim]",
        )
    else:
        console.print(
            "[green]✅ All configurations are consistent![/green]",
        )

    console.print()

    # Help text
    console.print(
        "[dim]Configure tool ordering in pyproject.toml under [tool.lintro]:[/dim]",
    )
    console.print(
        '[dim]  tool_order = "priority" | "alphabetical" | "custom"[/dim]',
    )
    console.print(
        '[dim]  tool_order_custom = ["prettier", "black", "ruff", ...][/dim]',
    )
    console.print(
        "[dim]  tool_priorities = { ruff = 5, black = 10 }[/dim]",
    )
