"""Additional tests for `lintro.utils.tool_executor` coverage.

These tests focus on unhit branches in the simple executor:
- `_get_tools_to_run` edge cases and validation
- Main-loop error handling when resolving tools
- Early post-checks filtering removing tools from the main phase
- Post-checks behavior for unknown tool names
- Output persistence error handling
"""

from __future__ import annotations

import json
from typing import Any, Never

from assertpy import assert_that

from lintro.models.core.tool_result import ToolResult
from lintro.utils.tool_executor import run_lint_tools_simple


class _EnumLike:
    def __init__(self, name: str) -> None:
        self.name = name


def _stub_logger(monkeypatch) -> None:
    import lintro.utils.console_logger as cl

    class SilentLogger:
        def __getattr__(self, name: str):  # noqa: D401 - test stub
            def _(*a: Any, **k: Any) -> None:
                return None

            return _

    monkeypatch.setattr(cl, "create_logger", lambda *a, **k: SilentLogger())


def test_get_tools_to_run_unknown_tool_raises(monkeypatch) -> None:
    """Unknown tool name should raise ValueError.

    Args:
        monkeypatch: Pytest fixture to modify objects during the test.
    """
    import lintro.utils.tool_executor as te

    _stub_logger(monkeypatch)

    # Use real function; only patch manager lookups to be harmless if called
    monkeypatch.setattr(
        te.tool_manager,
        "get_check_tools",
        lambda: {},
        raising=True,
    )

    try:
        _ = te._get_tools_to_run(tools="notatool", action="check")
        assert False, "Expected ValueError for unknown tool"
    except ValueError as e:  # noqa: PT017
        assert_that(str(e)).contains("Unknown tool")


def test_get_tools_to_run_fmt_with_cannot_fix_raises(monkeypatch) -> None:
    """Selecting a non-fix tool for fmt should raise a validation error.

    Args:
        monkeypatch: Pytest fixture to modify objects during the test.
    """
    import lintro.utils.tool_executor as te

    _stub_logger(monkeypatch)

    class NoFixTool:
        can_fix = False

        def set_options(self, **kwargs) -> None:  # noqa: D401
            return None

    # Ensure we resolve a tool instance with can_fix False
    monkeypatch.setattr(
        te.tool_manager,
        "get_tool",
        lambda enum_val: NoFixTool(),
        raising=True,
    )

    # Directly call the helper
    try:
        _ = te._get_tools_to_run(tools="bandit", action="fmt")
        assert False, "Expected ValueError for non-fix tool in fmt"
    except ValueError as e:  # noqa: PT017
        assert_that(str(e)).contains("does not support formatting")


def test_main_loop_get_tool_raises_appends_failure(monkeypatch, capsys) -> None:
    """If a tool cannot be resolved, a failure result is appended and run continues.

    Args:
        monkeypatch: Pytest fixture to modify objects during the test.
        capsys: Pytest fixture to capture stdout/stderr for assertions.
    """
    _stub_logger(monkeypatch)

    import lintro.utils.tool_executor as te

    ok = ToolResult(name="black", success=True, output="", issues_count=0)

    def fake_get_tools(*, tools: str | None, action: str):
        return [_EnumLike("RUFF"), _EnumLike("BLACK")]

    def fake_get_tool(enum_val):
        if enum_val.name.lower() == "ruff":
            raise RuntimeError("ruff not available")
        return type(
            "_T",
            (),
            {  # simple stub
                "name": "black",
                "can_fix": True,
                "set_options": lambda self, **k: None,
                "check": lambda self, paths: ok,
                "fix": lambda self, paths: ok,
                "options": {},
            },
        )()

    monkeypatch.setattr(te, "_get_tools_to_run", fake_get_tools, raising=True)
    monkeypatch.setattr(te.tool_manager, "get_tool", fake_get_tool, raising=True)
    monkeypatch.setattr(
        te.OutputManager,
        "write_reports_from_results",
        lambda self, results: None,
        raising=True,
    )

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
    out = capsys.readouterr().out
    data = json.loads(out)
    tool_names = [r.get("tool") for r in data.get("results", [])]
    assert_that("ruff" in tool_names).is_true()
    # Exit should be failure due to appended failure result
    assert_that(code).is_equal_to(1)


def test_write_reports_errors_are_swallowed(monkeypatch) -> None:
    """Errors while saving outputs should not crash or change exit semantics.

    Args:
        monkeypatch: Pytest fixture to modify objects during the test.
    """
    _stub_logger(monkeypatch)

    import lintro.utils.tool_executor as te

    ok = ToolResult(name="ruff", success=True, output="", issues_count=0)

    def fake_get_tools(*, tools: str | None, action: str):
        return [_EnumLike("RUFF")]

    ruff_tool = type(
        "_T",
        (),
        {
            "name": "ruff",
            "can_fix": True,
            "set_options": lambda self, **k: None,
            "check": lambda self, paths: ok,
            "fix": lambda self, paths: ok,
            "options": {},
        },
    )()

    monkeypatch.setattr(te, "_get_tools_to_run", fake_get_tools, raising=True)
    monkeypatch.setattr(te.tool_manager, "get_tool", lambda e: ruff_tool)

    def boom(self, results) -> Never:
        raise RuntimeError("disk full")

    monkeypatch.setattr(
        te.OutputManager,
        "write_reports_from_results",
        boom,
        raising=True,
    )

    code = run_lint_tools_simple(
        action="check",
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


def test_unknown_post_check_tool_is_skipped(monkeypatch) -> None:
    """Unknown post-check tool names should be warned and skipped gracefully.

    Args:
        monkeypatch: Pytest fixture to modify objects during the test.
    """
    _stub_logger(monkeypatch)

    import lintro.utils.tool_executor as te

    ok = ToolResult(name="ruff", success=True, output="", issues_count=0)
    ruff_tool = type(
        "_T",
        (),
        {
            "name": "ruff",
            "can_fix": True,
            "set_options": lambda self, **k: None,
            "check": lambda self, paths: ok,
            "fix": lambda self, paths: ok,
            "options": {},
        },
    )()

    monkeypatch.setattr(
        te,
        "_get_tools_to_run",
        lambda tools, action: [_EnumLike("RUFF")],
        raising=True,
    )
    monkeypatch.setattr(te.tool_manager, "get_tool", lambda e: ruff_tool)
    monkeypatch.setattr(
        te,
        "load_post_checks_config",
        lambda: {"enabled": True, "tools": ["notatool"], "enforce_failure": False},
        raising=True,
    )

    code = run_lint_tools_simple(
        action="check",
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


def test_post_checks_early_filter_removes_black_from_main(monkeypatch) -> None:
    """Black should be excluded from main phase when configured as post-check.

    Args:
        monkeypatch: Pytest fixture to modify objects during the test.
    """
    import lintro.utils.tool_executor as te

    class LoggerCapture:
        def __init__(self) -> None:
            self.tools_list = None

        def __getattr__(self, name: str):  # default no-ops
            def _(*a: Any, **k: Any) -> None:
                return None

            return _

        def print_lintro_header(
            self,
            *,
            action: str,
            tool_count: int,
            tools_list: str,
        ) -> None:
            self.tools_list = tools_list
            return None

    logger = LoggerCapture()
    monkeypatch.setattr(te, "create_logger", lambda **k: logger, raising=True)

    # Tools initially include ruff and black
    monkeypatch.setattr(
        te,
        "_get_tools_to_run",
        lambda tools, action: [_EnumLike("RUFF"), _EnumLike("BLACK")],
        raising=True,
    )
    # Early config marks black as post-check
    monkeypatch.setattr(
        te,
        "load_post_checks_config",
        lambda: {"enabled": True, "tools": ["black"], "enforce_failure": True},
        raising=True,
    )

    # Provide a no-op ruff tool
    ok = ToolResult(name="ruff", success=True, output="", issues_count=0)
    ruff_tool = type(
        "_T",
        (),
        {
            "name": "ruff",
            "can_fix": True,
            "set_options": lambda self, **k: None,
            "check": lambda self, paths: ok,
            "fix": lambda self, paths: ok,
            "options": {},
        },
    )()
    monkeypatch.setattr(
        te.tool_manager,
        "get_tool",
        lambda enum_val: ruff_tool,
        raising=True,
    )
    monkeypatch.setattr(
        te.OutputManager,
        "write_reports_from_results",
        lambda self, results: None,
        raising=True,
    )

    code = run_lint_tools_simple(
        action="check",
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
    # Ensure black is not in main-phase header list
    assert_that(logger.tools_list).is_not_none()
    assert_that("black" in (logger.tools_list or "")).is_false()


def test_all_filtered_results_in_no_tools_warning(monkeypatch) -> None:
    """If filtering removes all tools, executor should return failure gracefully.

    Args:
        monkeypatch: Pytest fixture to modify objects during the test.
    """
    _stub_logger(monkeypatch)

    import lintro.utils.tool_executor as te

    # Start with only black
    monkeypatch.setattr(
        te,
        "_get_tools_to_run",
        lambda tools, action: [_EnumLike("BLACK")],
        raising=True,
    )
    # Early config filters out black
    monkeypatch.setattr(
        te,
        "load_post_checks_config",
        lambda: {"enabled": True, "tools": ["black"], "enforce_failure": True},
        raising=True,
    )

    code = run_lint_tools_simple(
        action="check",
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
    assert_that(code).is_equal_to(1)
