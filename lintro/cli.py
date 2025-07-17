"""Command-line interface for Lintro."""

import click
from lintro import __version__
from lintro.cli_utils.commands.check import check_command
from lintro.cli_utils.commands.fmt import fmt_command
from lintro.cli_utils.commands.list_tools import list_tools_command
from lintro.utils.logging_utils import get_logger

# Initialize logger at CLI startup
get_logger()


@click.group()
@click.version_option(version=__version__)
def cli():
    """Lintro - A unified CLI tool for code formatting, linting, and quality assurance.

    Commands:
      check/format - Check code quality without making changes
      fmt/chk      - Auto-fix formatting issues across all supported files (respects .lintro-ignore)
      list-tools/ls - Show available tools and their capabilities
    """
    pass


# Add main commands
cli.add_command(check_command)
cli.add_command(fmt_command)
cli.add_command(list_tools_command)

# Add command aliases for consistency
cli.add_command(check_command, name="format")
cli.add_command(check_command, name="chk")
cli.add_command(list_tools_command, name="ls")


def main():
    """Entry point for the CLI."""
    cli()
