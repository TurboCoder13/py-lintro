"""Unit tests for CLI entrypoint command listing and aliases."""

from __future__ import annotations

from assertpy import assert_that
from click.testing import CliRunner

from lintro.cli import cli


def test_cli_lists_commands_and_aliases():
    """Ensure help lists primary commands and their common aliases."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("check")
    assert_that(result.output).contains("format")
    assert_that(result.output).contains("list-tools")
    assert_that(result.output).contains("chk")
    assert_that(result.output).contains("fmt")
    assert_that(result.output).contains("ls")
