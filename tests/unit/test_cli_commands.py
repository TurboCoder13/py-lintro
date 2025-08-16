from __future__ import annotations

from click.testing import CliRunner

from lintro.cli import cli


def test_cli_lists_commands_and_aliases():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    # Ensure canonical commands present
    assert "check" in result.output
    assert "format" in result.output
    assert "list-tools" in result.output
    # Ensure aliases are shown (registered)
    assert "chk" in result.output
    assert "fmt" in result.output
    assert "ls" in result.output
