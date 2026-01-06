"""Command-line interface for Lintro."""

from typing import Any, cast

import click
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lintro import __version__
from lintro.cli_utils.commands.check import check_command
from lintro.cli_utils.commands.config import config_command
from lintro.cli_utils.commands.format import format_command
from lintro.cli_utils.commands.init import init_command
from lintro.cli_utils.commands.list_tools import list_tools_command
from lintro.cli_utils.commands.test import test_command
from lintro.cli_utils.commands.versions import versions_command


class LintroGroup(click.Group):
    """Custom Click group with enhanced help rendering and command chaining.

    This group prints command aliases alongside their canonical names to make
    the CLI help output more discoverable. It also supports command chaining
    with comma-separated commands (e.g., lintro fmt , chk , tst).
    """

    def format_help(
        self,
        ctx: click.Context,
        formatter: click.HelpFormatter,
    ) -> None:
        """Render help with Rich formatting.

        Args:
            ctx: click.Context: The Click context.
            formatter: click.HelpFormatter: The help formatter (unused, we use Rich).
        """
        console = Console()

        # Header panel
        header = Text()
        header.append("🔧 Lintro", style="bold cyan")
        header.append(f" v{__version__}", style="dim")
        console.print(Panel(header, border_style="cyan"))
        console.print()

        # Description
        console.print(
            "[white]Unified CLI for code formatting, linting, "
            "and quality assurance.[/white]",
        )
        console.print()

        # Usage
        console.print("[bold cyan]Usage:[/bold cyan]")
        console.print("  lintro [OPTIONS] COMMAND [ARGS]...")
        console.print("  lintro COMMAND1 , COMMAND2 , ...  [dim](chain commands)[/dim]")
        console.print()

        # Commands table
        commands = self.list_commands(ctx)
        canonical_map: dict[str, tuple[click.Command, list[str]]] = {}
        for name in commands:
            cmd = self.get_command(ctx, name)
            if cmd is None:
                continue
            cmd_any = cast(Any, cmd)
            if not hasattr(cmd_any, "_canonical_name"):
                cmd_any._canonical_name = name
            canonical = cast(str, getattr(cmd_any, "_canonical_name", name))
            if canonical not in canonical_map:
                canonical_map[canonical] = (cmd, [])
            if name != canonical:
                canonical_map[canonical][1].append(name)

        table = Table(title="Commands", show_header=True, header_style="bold cyan")
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Alias", style="yellow", no_wrap=True)
        table.add_column("Description", style="white")

        for canonical, (cmd, aliases) in sorted(canonical_map.items()):
            alias_str = ", ".join(aliases) if aliases else "-"
            table.add_row(canonical, alias_str, cmd.get_short_help_str())

        console.print(table)
        console.print()

        # Options
        console.print("[bold cyan]Options:[/bold cyan]")
        console.print("  [yellow]--version[/yellow]  Show the version and exit.")
        console.print("  [yellow]--help[/yellow]     Show this message and exit.")
        console.print()

        # Examples
        console.print("[bold cyan]Examples:[/bold cyan]")
        console.print("  [dim]# Check all files[/dim]")
        console.print("  lintro check .")
        console.print()
        console.print("  [dim]# Format and then check[/dim]")
        console.print("  lintro fmt . , chk .")
        console.print()
        console.print("  [dim]# Show tool versions[/dim]")
        console.print("  lintro versions")

    def format_commands(
        self,
        ctx: click.Context,
        formatter: click.HelpFormatter,
    ) -> None:
        """Render command list with aliases in the help output.

        Args:
            ctx: click.Context: The Click context.
            formatter: click.HelpFormatter: The help formatter to write to.
        """
        # This is now handled by format_help, but keep for compatibility
        pass

    def invoke(
        self,
        ctx: click.Context,
    ) -> int:
        """Handle command execution with support for command chaining.

        Supports chaining commands with commas, e.g.: lintro fmt , chk , tst

        Args:
            ctx: click.Context: The Click context.

        Returns:
            int: Exit code from command execution.

        Raises:
            KeyboardInterrupt: If the user interrupts command execution.
            SystemExit: If a command exits with a non-zero exit code.
        """
        all_args = ctx.protected_args + ctx.args
        if all_args:
            # Get set of known command names/aliases
            command_names = set(self.list_commands(ctx))
            normalized_args: list[str] = []
            saw_separator = False

            for arg in all_args:
                if arg == ",":
                    normalized_args.append(arg)
                    saw_separator = True
                    continue

                if "," in arg:
                    # Check if this looks like comma-separated commands
                    raw_parts = [part.strip() for part in arg.split(",")]
                    # Filter out empty fragments after splitting
                    fragments = [part for part in raw_parts if part]
                    # Only split if all parts are known commands
                    if fragments and all(part in command_names for part in fragments):
                        # Split into separate tokens
                        for idx, part in enumerate(fragments):
                            if part:
                                normalized_args.append(part)
                            if idx < len(fragments) - 1:
                                normalized_args.append(",")
                                saw_separator = True
                        continue
                    # Not all parts are commands, keep as-is (e.g., --tools ruff,bandit)
                    normalized_args.append(arg)
                    continue

                normalized_args.append(arg)

            if saw_separator:
                # Parse chained commands from normalized args
                command_groups: list[list[str]] = []
                current_group: list[str] = []

                for arg in normalized_args:
                    if arg == ",":
                        if current_group:
                            command_groups.append(current_group)
                            current_group = []
                        continue
                    current_group.append(arg)

                if current_group:
                    command_groups.append(current_group)

                # Execute each command group
                exit_codes: list[int] = []
                for cmd_args in command_groups:
                    if not cmd_args:
                        continue
                    # Create a new context for each command
                    ctx_copy = self.make_context(
                        ctx.info_name,
                        cmd_args,
                        parent=ctx,
                        allow_extra_args=True,
                        allow_interspersed_args=False,
                    )
                    # Invoke the command
                    with ctx_copy.scope() as subctx:
                        try:
                            result = super().invoke(subctx)
                            exit_codes.append(result if isinstance(result, int) else 0)
                        except SystemExit as e:
                            exit_codes.append(
                                (
                                    e.code
                                    if isinstance(e.code, int)
                                    else (0 if e.code is None else 1)
                                ),
                            )
                        except KeyboardInterrupt:
                            # Re-raise KeyboardInterrupt to allow normal interruption
                            raise
                        except Exception as e:
                            # Catch all other exceptions to allow command chain to
                            # continue
                            exit_code = getattr(e, "exit_code", 1)
                            exit_codes.append(exit_code)
                            # Log the exception with full traceback
                            logger.exception(
                                (
                                    f"Error executing command "
                                    f"'{' '.join(cmd_args)}': {type(e).__name__}: {e}"
                                ),
                            )
                            # Also echo to stderr for immediate user feedback
                            click.echo(
                                click.style(
                                    (
                                        f"Error executing command "
                                        f"'{' '.join(cmd_args)}': "
                                        f"{type(e).__name__}: {e}"
                                    ),
                                    fg="red",
                                ),
                                err=True,
                            )

                # Return aggregated exit code (0 only if all succeeded)
                final_exit_code = max(exit_codes) if exit_codes else 0
                if final_exit_code != 0:
                    raise SystemExit(final_exit_code)
                return 0

        # Normal single command execution
        result = super().invoke(ctx)
        return int(result) if isinstance(result, int) else 0


@click.group(cls=LintroGroup, invoke_without_command=True)
@click.version_option(version=__version__)
def cli() -> None:
    """Lintro: Unified CLI for code formatting, linting, and quality assurance."""
    pass


# Register canonical commands and set _canonical_name for help
cast(Any, check_command)._canonical_name = "check"
cast(Any, config_command)._canonical_name = "config"
cast(Any, format_command)._canonical_name = "format"
cast(Any, init_command)._canonical_name = "init"
cast(Any, test_command)._canonical_name = "test"
cast(Any, list_tools_command)._canonical_name = "list-tools"
cast(Any, versions_command)._canonical_name = "versions"

cli.add_command(check_command, name="check")
cli.add_command(config_command, name="config")
cli.add_command(format_command, name="format")
cli.add_command(init_command, name="init")
cli.add_command(test_command, name="test")
cli.add_command(list_tools_command, name="list-tools")
cli.add_command(versions_command, name="versions")

# Register aliases
cli.add_command(check_command, name="chk")
cli.add_command(config_command, name="cfg")
cli.add_command(format_command, name="fmt")
cli.add_command(test_command, name="tst")
cli.add_command(list_tools_command, name="ls")
cli.add_command(versions_command, name="ver")


def main() -> None:
    """Entry point for the CLI."""
    cli()
