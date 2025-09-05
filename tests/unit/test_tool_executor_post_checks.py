from __future__ import annotations

import json

from assertpy import assert_that

from lintro.models.core.tool_result import ToolResult
from lintro.utils.tool_executor import run_lint_tools_simple


class FakeTool:
    def __init__(self, name: str, can_fix: bool, result: ToolResult):
        self.name = name
        self.can_fix = can_fix
        self._result = result
        self.options: dict[str, object] = {}

    def set_options(self, **kwargs):
        self.options.update(kwargs)

    def check(self, paths):
        return self._result

    def fix(self, paths):
        return self._result


class _EnumLike:
    def __init__(self, name: str):
        self.name = name


def _stub_logger(monkeypatch):
    import lintro.utils.console_logger as cl

    class SilentLogger:
        def __getattr__(self, name):
            def _(*a, **k):
                return None

            return _

    monkeypatch.setattr(cl, "create_logger", lambda *a, **k: SilentLogger())


def _setup_main_tool(monkeypatch):
    import lintro.utils.tool_executor as te

    ok = ToolResult(name="ruff", success=True, output="", issues_count=0)
    ruff = FakeTool("ruff", can_fix=True, result=ok)

    def fake_get_tools(*, tools: str | None, action: str):
        return [_EnumLike("RUFF")]

    monkeypatch.setattr(te, "_get_tools_to_run", fake_get_tools, raising=True)
    monkeypatch.setattr(te.tool_manager, "get_tool", lambda e: ruff, raising=True)

    def noop_write_reports_from_results(self, results):
        return None

    monkeypatch.setattr(
        te.OutputManager,
        "write_reports_from_results",
        noop_write_reports_from_results,
        raising=True,
    )

    return ruff


def test_post_checks_enforce_failure_on_unavailable_tool(monkeypatch):
    """When enforce_failure is True, missing post-check yields failure exit.

    This exercises the exception path in the post-check loop where resolving the
    tool raises and the executor appends a failure ToolResult when running check.

    Args:
        monkeypatch: Pytest fixture to modify objects during the test.
    """
    _stub_logger(monkeypatch)
    ruff_local = _setup_main_tool(monkeypatch)

    import lintro.utils.tool_executor as te

    # Post-checks enabled for black; enforce failure on check
    monkeypatch.setattr(
        te,
        "load_post_checks_config",
        lambda: {"enabled": True, "tools": ["black"], "enforce_failure": True},
        raising=True,
    )

    # Make black unavailable during post-check resolution
    def fail_get_tool(enum_val):
        # Fail only for the post-check tool (black); allow main ruff to run
        if getattr(enum_val, "name", "").lower() == "black":
            raise RuntimeError("black not available")
        return ruff_local

    monkeypatch.setattr(te.tool_manager, "get_tool", fail_get_tool, raising=True)

    code = run_lint_tools_simple(
        action="check",
        paths=["."],
        tools="all",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="auto",
        output_format="json",
        verbose=False,
        raw_output=False,
    )
    assert_that(code).is_equal_to(1)


def test_post_checks_missing_tool_no_enforce_skips(monkeypatch, capsys):
    """When enforce_failure is False, missing post-check is skipped gracefully.

    We validate behavior by inspecting JSON output rather than exit code, to
    avoid coupling to unrelated exit conditions. The main tool (ruff) should
    run, and the missing post-check tool (black) should not appear in results.

    Args:
        monkeypatch: Pytest fixture to modify objects during the test.
        capsys: Pytest fixture to capture stdout/stderr for assertions.
    """
    _stub_logger(monkeypatch)
    _setup_main_tool(monkeypatch)

    import lintro.utils.tool_executor as te

    monkeypatch.setattr(
        te,
        "load_post_checks_config",
        lambda: {"enabled": True, "tools": ["black"], "enforce_failure": False},
        raising=True,
    )

    def fail_get_tool(enum_val):
        raise RuntimeError("black not available")

    monkeypatch.setattr(te.tool_manager, "get_tool", fail_get_tool, raising=True)

    _ = run_lint_tools_simple(
        action="check",
        paths=["."],
        tools="all",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="auto",
        output_format="json",
        verbose=False,
        raw_output=False,
    )
    out = capsys.readouterr().out
    data = json.loads(out)
    tools_list = data.get("tools", [])
    assert_that("ruff" in tools_list).is_true()
    assert_that("black" in tools_list).is_false()
