"""Programmatic invocation tests for CLI command functions."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.cli_utils.commands.check import check as check_prog
from lintro.cli_utils.commands.format import format_code_legacy


def test_check_programmatic_success(monkeypatch):
    """Programmatic check returns None on success.

    Args:
        monkeypatch: Pytest monkeypatch fixture to stub executor return.
    """
    import lintro.cli_utils.commands.check as check_mod

    monkeypatch.setattr(check_mod, "run_lint_tools_simple", lambda **k: 0, raising=True)
    assert_that(
        check_prog(
            paths=["."],
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
        ),
    ).is_none()


def test_format_programmatic_success(monkeypatch):
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
    assert_that(
        format_code_legacy(
            paths=["."],
            tools="prettier",
            tool_options=None,
            exclude=None,
            include_venv=False,
            group_by="auto",
            output_format="grid",
            verbose=False,
        ),
    ).is_none()


def test_format_programmatic_failure_raises(monkeypatch):
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
    with pytest.raises(Exception):
        format_code_legacy(
            paths=["."],
            tools="prettier",
            tool_options=None,
            exclude=None,
            include_venv=False,
            group_by="auto",
            output_format="grid",
            verbose=False,
        )
