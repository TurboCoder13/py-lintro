"""Environment report rendering utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel

from lintro.utils.environment._protocol import Renderable
from lintro.utils.environment.environment_report import EnvironmentReport

if TYPE_CHECKING:
    from rich.console import Console

# Consistent label width for alignment (matches original output)
LABEL_WIDTH = 12


def render_section(console: Console, section: Renderable | None) -> None:
    """Render a single environment section to the console.

    Args:
        console: Rich console for output.
        section: Environment section implementing Renderable protocol,
                 or None for optional sections.
    """
    if section is None:
        return

    if not section.is_available():
        console.print(f"[bold cyan]{section.section_title}:[/bold cyan]")
        console.print("  [dim](not installed)[/dim]")
        console.print()
        return

    console.print(f"[bold cyan]{section.section_title}:[/bold cyan]")
    for label, value in section.to_display_rows():
        # Pad label for alignment
        padded_label = f"{label}:".ljust(LABEL_WIDTH)
        console.print(f"  {padded_label} {value}")
    console.print()


def _render_env_vars(console: Console, env_vars: dict[str, str | None]) -> None:
    """Render environment variables section.

    Args:
        console: Rich console for output.
        env_vars: Dictionary of environment variable names to values.
    """
    console.print("[bold cyan]Environment Variables:[/bold cyan]")
    for var_name, var_value in env_vars.items():
        display_value: str
        if var_name == "PATH" and var_value:
            # Truncate PATH for readability
            display_value = var_value[:60] + "..." if len(var_value) > 60 else var_value
        else:
            display_value = var_value or "(not set)"
        console.print(f"  {var_name}: {display_value}")
    console.print()


def render_environment_report(console: Console, env: EnvironmentReport) -> None:
    """Render complete environment report to the console.

    This is a drop-in replacement for the old _print_environment_report()
    function, providing identical output using the Renderable protocol.

    Args:
        console: Rich console for output.
        env: Complete environment report.
    """
    console.print(
        Panel.fit(
            "[bold]Lintro Environment Report[/bold]",
            border_style="cyan",
        ),
    )
    console.print()

    # Render each section in order
    sections: list[Renderable | None] = [
        env.lintro,
        env.system,
        env.python,
        env.node,
        env.rust,
        env.go,
        env.ruby,
        env.project,
        env.ci,
    ]

    for section in sections:
        render_section(console, section)

    # Environment variables are handled specially (dict, not dataclass)
    _render_env_vars(console, env.env_vars)
