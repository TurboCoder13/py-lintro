"""Command-line interface for Lintro."""

import click
from loguru import logger

from lintro import __version__
from lintro.cli_utils.commands.check import check_command
from lintro.cli_utils.commands.format import format_code
from lintro.cli_utils.commands.list_tools import list_tools_command
from lintro.cli_utils.commands.test import test_command


class LintroGroup(click.Group):
    """Custom Click group with enhanced help rendering and command chaining.

    This group prints command aliases alongside their canonical names to make
    the CLI help output more discoverable. It also supports command chaining
    with comma-separated commands (e.g., lintro fmt , chk , tst).
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
        return super().invoke(ctx)


@click.group(cls=LintroGroup, invoke_without_command=True)
@click.version_option(version=__version__)
def cli() -> None:
    """Lintro: Unified CLI for code formatting, linting, and quality assurance."""
    pass


# Register canonical commands and set _canonical_name for help
check_command._canonical_name = "check"
format_code._canonical_name = "format"
test_command._canonical_name = "test"
list_tools_command._canonical_name = "list-tools"

cli.add_command(check_command, name="check")
cli.add_command(format_code, name="format")
cli.add_command(test_command, name="test")
cli.add_command(list_tools_command, name="list-tools")

# Register aliases
cli.add_command(check_command, name="chk")
cli.add_command(format_code, name="fmt")
cli.add_command(test_command, name="tst")
cli.add_command(list_tools_command, name="ls")


def main() -> None:
    """Entry point for the CLI."""
    cli()
