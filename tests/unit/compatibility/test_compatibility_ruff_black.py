"""Compatibility tests ensuring Ruff/Black policy interactions."""

from __future__ import annotations

from assertpy import assert_that

from lintro.models.core.tool_result import ToolResult
from lintro.utils.tool_executor import run_lint_tools_simple


class FakeTool:
    """Simple stub representing a tool with check/fix capability."""

    def __init__(self, name: str, can_fix: bool) -> None:
        """Initialize stub tool.

        Args:
            name: Tool name.
            can_fix: Whether the tool can apply fixes.
        """
        self.name = name
        self.can_fix = can_fix
        self.options = {}

    def set_options(self, **kwargs) -> None:
        """Record provided options for later assertions.

        Args:
            **kwargs: Arbitrary option key-value pairs forwarded by the runner.
        """
        self.options.update(kwargs)

    def check(self, paths):
        """Return a successful empty result for lint checks.

        Args:
            paths: Target file or directory paths to check.

        Returns:
            ToolResult indicating success with zero issues.
        """
        return ToolResult(name=self.name, success=True, output="", issues_count=0)

    def fix(self, paths):
        """Return a successful empty result for fixes.

        Args:
            paths: Target file or directory paths to fix.

        Returns:
            ToolResult indicating success with zero issues.
        """
        return ToolResult(name=self.name, success=True, output="", issues_count=0)


class _EnumLike:
    """Tiny stand-in for enum entries returned by tool discovery."""

    def __init__(self, name: str) -> None:
        self.name = name


def _stub_logger(monkeypatch) -> None:
    """Silence console logger for deterministic tests.

    Args:
        monkeypatch: Pytest monkeypatch fixture for patching objects.
    """
    import lintro.utils.console_logger as cl

    class SilentLogger:
        def __getattr__(self, name):
            def _(*a, **k) -> None:
                return None

            return _

    monkeypatch.setattr(cl, "create_logger", lambda *a, **k: SilentLogger())


def _setup_tools(monkeypatch):
    """Prepare stubbed tool manager and output manager plumbing.

    Args:
        monkeypatch: Pytest monkeypatch fixture for patching objects.

    Returns:
        Tuple of stubbed Ruff and Black tool instances.
    """
    import lintro.utils.tool_executor as te

    ruff = FakeTool("ruff", can_fix=True)
    black = FakeTool("black", can_fix=True)
    tool_map = {"ruff": ruff, "black": black}

    def fake_get_tools(tools: str | None, action: str):
        """Return enum-like entries for ruff and black in order.

        Args:
            tools: Optional tool selection string (ignored in tests).
            action: Runner action being executed (e.g., "fmt" or "check").

        Returns:
            list[_EnumLike]: Entries representing Ruff then Black.
        """
        return [_EnumLike("RUFF"), _EnumLike("BLACK")]

    monkeypatch.setattr(te, "_get_tools_to_run", fake_get_tools, raising=True)
    monkeypatch.setattr(te.tool_manager, "get_tool", lambda e: tool_map[e.name.lower()])

    def noop_write_reports_from_results(self, results) -> None:
        """No-op writer used to avoid filesystem interaction.

        Args:
            self: Output manager instance under test.
            results: Aggregated tool results to write.

        Returns:
            None.
        """
        return None

    monkeypatch.setattr(
        te.OutputManager,
        "write_reports_from_results",
        noop_write_reports_from_results,
    )

    return ruff, black


def test_ruff_formatting_disabled_when_black_present(monkeypatch) -> None:
    """Black present: Ruff formatting should be disabled by default.

    Args:
        monkeypatch: Pytest monkeypatch fixture for patching objects.
    """
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


def test_ruff_formatting_respects_cli_override(monkeypatch) -> None:
    """CLI options should re-enable Ruff format and format_check.

    Args:
        monkeypatch: Pytest monkeypatch fixture for patching objects.
    """
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


def test_ruff_format_check_disabled_in_check_when_black_present(monkeypatch) -> None:
    """Black present: Ruff format_check should be disabled in check.

    Args:
        monkeypatch: Pytest monkeypatch fixture for patching objects.
    """
    _stub_logger(monkeypatch)
    ruff, black = _setup_tools(monkeypatch)

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
    assert_that(ruff.options.get("format_check")).is_false()
