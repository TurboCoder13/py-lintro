from __future__ import annotations

from click.testing import CliRunner

from lintro.cli_utils.commands.check import check_command
from lintro.cli_utils.commands.format import format_code
from lintro.cli_utils.commands.list_tools import list_tools_command


def test_check_invokes_executor(monkeypatch):
    calls = {}
    # Patch the imported symbol inside the command module
    import lintro.cli_utils.commands.check as check_mod

    def fake_run(**kwargs):
        calls.update(kwargs)
        return 0

    monkeypatch.setattr(check_mod, "run_lint_tools_simple", lambda **k: fake_run(**k))

    runner = CliRunner()
    result = runner.invoke(check_command, ["--tools", "ruff", "."])
    assert result.exit_code == 0
    assert calls.get("action") == "check"


def test_format_invokes_executor(monkeypatch):
    calls = {}
    import lintro.cli_utils.commands.format as format_mod

    def fake_run(**kwargs):
        calls.update(kwargs)
        return 0

    monkeypatch.setattr(format_mod, "run_lint_tools_simple", lambda **k: fake_run(**k))

    runner = CliRunner()
    result = runner.invoke(format_code, ["--tools", "prettier", "."])
    assert result.exit_code == 0
    assert calls.get("action") == "fmt"


def test_list_tools_outputs(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(list_tools_command, [])
    assert result.exit_code == 0
    # Ensure header and summary present
    assert "Available Tools" in result.output
    assert "Total tools:" in result.output
