"""Programmatic invocation tests for CLI command functions."""

from __future__ import annotations

import pytest

from lintro.cli_utils.commands.check import check as check_prog
from lintro.cli_utils.commands.format import format_code


def test_check_programmatic_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Programmatic check returns None on success.

    Args:
        monkeypatch: Pytest monkeypatch fixture to stub executor return.
    """
    import lintro.cli_utils.commands.check as check_mod

    monkeypatch.setattr(check_mod, "run_lint_tools_simple", lambda **k: 0, raising=True)
    # check() returns None on success, call without assignment
    check_prog(
        paths=(".",),
        tools="ruff",
        tool_options=None,
        exclude=None,
        include_venv=False,
        output=None,
        output_format="grid",
        group_by="auto",
        ignore_conflicts=False,
        verbose=False,
        no_log=False,
    )


def test_format_programmatic_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Programmatic format returns None on success.

    Args:
        monkeypatch: Pytest monkeypatch fixture to stub executor return.
    """
    import lintro.cli_utils.commands.format as format_mod

    monkeypatch.setattr(
        format_mod,
        "run_lint_tools_simple",
        lambda **k: 0,
        raising=True,
    )
    # format_code() returns None on success, call without assignment
    format_code(
        paths=["."],
        tools="prettier",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="auto",
        output_format="grid",
        verbose=False,
    )


def test_format_programmatic_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Programmatic format raises when executor returns non-zero.

    Args:
        monkeypatch: Pytest monkeypatch fixture to stub executor return.
    """
    import lintro.cli_utils.commands.format as format_mod

    monkeypatch.setattr(
        format_mod,
        "run_lint_tools_simple",
        lambda **k: 1,
        raising=True,
    )
    with pytest.raises(RuntimeError):
        format_code(
            paths=["."],
            tools="prettier",
            tool_options=None,
            exclude=None,
            include_venv=False,
            group_by="auto",
            output_format="grid",
            verbose=False,
        )
