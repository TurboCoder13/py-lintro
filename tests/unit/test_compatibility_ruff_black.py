from __future__ import annotations

from assertpy import assert_that

from lintro.models.core.tool_result import ToolResult
from lintro.utils.tool_executor import run_lint_tools_simple


class FakeTool:
    def __init__(self, name: str, can_fix: bool):
        self.name = name
        self.can_fix = can_fix
        self.options = {}

    def set_options(self, **kwargs):
        self.options.update(kwargs)

    def check(self, paths):
        return ToolResult(name=self.name, success=True, output="", issues_count=0)

    def fix(self, paths):
        return ToolResult(name=self.name, success=True, output="", issues_count=0)


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


def _setup_tools(monkeypatch):
    import lintro.utils.tool_executor as te

    ruff = FakeTool("ruff", can_fix=True)
    black = FakeTool("black", can_fix=True)
    tool_map = {"ruff": ruff, "black": black}

    def fake_get_tools(*, tools: str | None, action: str):
        return [_EnumLike("RUFF"), _EnumLike("BLACK")]

    monkeypatch.setattr(te, "_get_tools_to_run", fake_get_tools, raising=True)
    monkeypatch.setattr(te.tool_manager, "get_tool", lambda e: tool_map[e.name.lower()])

    def noop_write_reports_from_results(self, results):
        return None

    monkeypatch.setattr(
        te.OutputManager, "write_reports_from_results", noop_write_reports_from_results
    )

    return ruff, black


def test_ruff_formatting_disabled_when_black_present(monkeypatch):
    _stub_logger(monkeypatch)
    ruff, black = _setup_tools(monkeypatch)

    code = run_lint_tools_simple(
        action="fmt",
        paths=["."],
        tools="all",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="auto",
        output_format="grid",
        verbose=False,
        raw_output=False,
    )

    assert_that(code).is_equal_to(0)
    assert_that(ruff.options.get("format")).is_false()
    assert_that(ruff.options.get("format_check")).is_false()


def test_ruff_formatting_respects_cli_override(monkeypatch):
    _stub_logger(monkeypatch)
    ruff, black = _setup_tools(monkeypatch)

    code = run_lint_tools_simple(
        action="fmt",
        paths=["."],
        tools="all",
        tool_options="ruff:format=True,ruff:format_check=True",
        exclude=None,
        include_venv=False,
        group_by="auto",
        output_format="grid",
        verbose=False,
        raw_output=False,
    )

    assert_that(code).is_equal_to(0)
    assert_that(ruff.options.get("format")).is_true()
    assert_that(ruff.options.get("format_check")).is_true()
