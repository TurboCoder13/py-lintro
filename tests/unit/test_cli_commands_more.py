"""Unit tests exercising subcommand wiring for CLI commands."""

from __future__ import annotations

from assertpy import assert_that
from click.testing import CliRunner

from lintro.cli_utils.commands.check import check_command
from lintro.cli_utils.commands.format import format_code
from lintro.cli_utils.commands.list_tools import list_tools_command


def test_check_invokes_executor(monkeypatch):
    """Invoke check subcommand and verify executor receives parameters.

    Args:
        monkeypatch: Pytest monkeypatch fixture to stub executor call.
    """
    calls = {}
    import lintro.cli_utils.commands.check as check_mod

    def fake_run(**kwargs):
        calls.update(kwargs)
        return 0

    monkeypatch.setattr(check_mod, "run_lint_tools_simple", lambda **k: fake_run(**k))
    runner = CliRunner()
    result = runner.invoke(check_command, ["--tools", "ruff", "."])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(calls.get("action")).is_equal_to("check")


def test_format_invokes_executor(monkeypatch):
    """Invoke format subcommand and verify executor receives parameters.

    Args:
        monkeypatch: Pytest monkeypatch fixture to stub executor call.
    """
    calls = {}
    import lintro.cli_utils.commands.format as format_mod

    def fake_run(**kwargs):
        calls.update(kwargs)
        return 0

    monkeypatch.setattr(format_mod, "run_lint_tools_simple", lambda **k: fake_run(**k))
    runner = CliRunner()
    result = runner.invoke(format_code, ["--tools", "prettier", "."])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(calls.get("action")).is_equal_to("fmt")


def test_list_tools_outputs(monkeypatch):
    """Run list-tools command and validate expected text in output.

    Args:
        monkeypatch: Pytest monkeypatch fixture (not used).
    """
    runner = CliRunner()
    result = runner.invoke(list_tools_command, [])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("Available Tools")
    assert_that(result.output).contains("Total tools:")
