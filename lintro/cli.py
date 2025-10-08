"""Command-line interface for Lintro."""

import click

from lintro import __version__
from lintro.cli_utils.commands.check import check_command
from lintro.cli_utils.commands.format import format_code
from lintro.cli_utils.commands.list_tools import list_tools_command


class LintroGroup(click.Group):
    """Custom Click group with enhanced help rendering.

    This group prints command aliases alongside their canonical names to make
    the CLI help output more discoverable.
    """

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
        # Group commands by canonical name and aliases
        commands = self.list_commands(ctx)
        # Map canonical name to (command, [aliases])
        canonical_map = {}
        for name in commands:
            cmd = self.get_command(ctx, name)
            if not hasattr(cmd, "_canonical_name"):
                cmd._canonical_name = name
            canonical = cmd._canonical_name
            if canonical not in canonical_map:
                canonical_map[canonical] = (cmd, [])
            if name != canonical:
                canonical_map[canonical][1].append(name)
        rows = []
        for canonical, (cmd, aliases) in canonical_map.items():
            names = [canonical] + aliases
            name_str = " / ".join(names)
            rows.append((name_str, cmd.get_short_help_str()))
        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)


@click.group(cls=LintroGroup, invoke_without_command=True)
@click.version_option(version=__version__)
def cli() -> None:
    """Lintro: Unified CLI for code formatting, linting, and quality assurance."""
    pass


# Register canonical commands and set _canonical_name for help
check_command._canonical_name = "check"
format_code._canonical_name = "format"
list_tools_command._canonical_name = "list-tools"

cli.add_command(check_command, name="check")
cli.add_command(format_code, name="format")
cli.add_command(list_tools_command, name="list-tools")

# Register aliases
cli.add_command(check_command, name="chk")
cli.add_command(format_code, name="fmt")
cli.add_command(list_tools_command, name="ls")


def main() -> None:
    """Entry point for the CLI."""
    cli()
