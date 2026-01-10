"""Shared fixtures for CommandChainer tests."""

from __future__ import annotations

import click
import pytest


@pytest.fixture
def mock_group() -> click.Group:
    """Create a mock Click group with test commands.

    Returns:
        click.Group: A Click group with fmt, chk, and tst commands.
    """

    @click.group()
    def cli() -> None:
        """Test CLI group."""
        pass

    @cli.command(name="fmt")
    @click.argument("paths", nargs=-1)
    def fmt_cmd(paths: tuple[str, ...]) -> int:
        """Format command.

        Args:
            paths: Paths to format.

        Returns:
            int: Exit code (always 0).
        """
        return 0

    @cli.command(name="chk")
    @click.argument("paths", nargs=-1)
    def chk_cmd(paths: tuple[str, ...]) -> int:
        """Check command.

        Args:
            paths: Paths to check.

        Returns:
            int: Exit code (always 0).
        """
        return 0

    @cli.command(name="tst")
    def tst_cmd() -> int:
        """Test command.

        Returns:
            int: Exit code (always 0).
        """
        return 0

    return cli
