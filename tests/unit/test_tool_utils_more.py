"""Additional tests for tool_utils formatting and walking behavior."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.pytest.pytest_issue import PytestIssue
from lintro.parsers.ruff.ruff_issue import RuffFormatIssue, RuffIssue
from lintro.tools.implementations.tool_prettier import PRETTIER_FILE_PATTERNS
from lintro.utils.tool_utils import (
    TOOL_TABLE_FORMATTERS,
    format_tool_output,
    walk_files_with_excludes,
)


def test_format_tool_output_with_parsed_issues_and_fixable_sections(
    monkeypatch,
) -> None:
    """Format tool output, including fixable issues section when present.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    import lintro.utils.tool_utils as tu

    def fake_tabulate(
        tabular_data,
        headers,
        tablefmt,
        stralign,
        disable_numparse,
    ) -> str:
        return "TABLE"

    monkeypatch.setattr(tu, "TABULATE_AVAILABLE", True, raising=True)
    monkeypatch.setattr(tu, "tabulate", fake_tabulate, raising=True)
    issues = [
        RuffIssue(
            file="a.py",
            line=1,
            column=1,
            code="E",
            message="m",
            url=None,
            end_line=1,
            end_column=2,
            fixable=False,
            fix_applicability=None,
        ),
        RuffFormatIssue(file="b.py"),
    ]
    txt = format_tool_output(
        tool_name="ruff",
        output="raw",
        group_by="auto",
        output_format="grid",
        issues=issues,
    )
    assert_that("Auto-fixable" in txt or txt == "TABLE").is_true()


def test_format_tool_output_parsing_fallbacks(monkeypatch) -> None:
    """Fallback to raw output for unknown tools or missing issues.

    Args:
        monkeypatch: Pytest monkeypatch fixture (not used).
    """
    out = format_tool_output(
        tool_name="unknown",
        output="some raw output",
        group_by="auto",
        output_format="grid",
        issues=None,
    )
    assert_that(out).is_equal_to("some raw output")


def test_walk_files_excludes_venv(tmp_path) -> None:
    """walk_files_with_excludes should omit venv directories by default.

    Args:
        tmp_path: pytest tmp_path fixture
    """
    root = tmp_path
    (root / ".venv" / "lib").mkdir(parents=True)
    (root / "pkg" / "mod").mkdir(parents=True)
    file_a = root / "pkg" / "mod" / "a.py"
    file_a.write_text("x=1\n")
    venv_file = root / ".venv" / "lib" / "b.py"
    venv_file.write_text("y=2\n")

    files = walk_files_with_excludes(
        paths=[str(root)],
        file_patterns=["*.py"],
        exclude_patterns=[],
        include_venv=False,
    )
    assert_that(str(file_a) in files).is_true()
    assert_that(str(venv_file) in files).is_false()


def test_tool_table_formatters_contains_pytest() -> None:
    """Test that TOOL_TABLE_FORMATTERS contains pytest entry.

    This ensures pytest issues can be formatted for display.
    """
    assert_that("pytest" in TOOL_TABLE_FORMATTERS).is_true()
    descriptor, formatter = TOOL_TABLE_FORMATTERS["pytest"]
    assert_that(descriptor).is_not_none()
    assert_that(formatter).is_not_none()


def test_format_tool_output_with_pytest_issues(monkeypatch) -> None:
    """Test format_tool_output with pytest test issues.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    import lintro.formatters.styles.grid as grid
    import lintro.utils.tool_utils as tu

    def fake_tabulate(
        tabular_data,
        headers,
        tablefmt,
        stralign,
        numalign=None,
        colalign=None,
        maxcolwidths=None,
        disable_numparse=False,
    ) -> str:
        return "PYTEST_TABLE"

    monkeypatch.setattr(tu, "TABULATE_AVAILABLE", True, raising=True)
    monkeypatch.setattr(grid, "TABULATE_AVAILABLE", True, raising=True)
    monkeypatch.setattr(grid, "tabulate", fake_tabulate, raising=True)

    pytest_issues = [
        PytestIssue(
            file="test_example.py",
            line=10,
            test_name="test_failure",
            message="AssertionError: Expected 1 but got 2",
            test_status="FAILED",
        ),
    ]

    txt = format_tool_output(
        tool_name="pytest",
        output="raw output",
        group_by="auto",
        output_format="grid",
        issues=pytest_issues,
    )

    # Should format using pytest formatter
    assert_that(txt).contains("PYTEST_TABLE")


def test_format_tool_output_pytest_raw_fallback(monkeypatch) -> None:
    """Test format_tool_output falls back to raw for pytest without tabulate.

    This ensures graceful degradation when tabulate is not available.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    import lintro.utils.tool_utils as tu

    # Force tabulate to be unavailable
    monkeypatch.setattr(tu, "TABULATE_AVAILABLE", False, raising=True)

    # Temporarily remove pytest from TOOL_TABLE_FORMATTERS so formatter path
    # doesn't execute, forcing fallback to raw output parsing path
    monkeypatch.delitem(TOOL_TABLE_FORMATTERS, "pytest", raising=False)

    pytest_issues = [
        PytestIssue(
            file="test_example.py",
            line=10,
            test_name="test_failure",
            message="AssertionError",
            test_status="FAILED",
        ),
    ]

    # Call with tabulate unavailable and formatter path disabled
    # This will go to parsing path, and if parsing fails, return raw output
    txt = format_tool_output(
        tool_name="pytest",
        output="raw pytest output",
        group_by="auto",
        output_format="grid",
        issues=pytest_issues,
    )

    # Should fall back to raw output when formatter path is unavailable
    assert_that(txt).is_equal_to("raw pytest output")


def test_prettier_file_patterns_include_yaml() -> None:
    """Ensure Prettier continues to format YAML files."""
    assert_that("*.yaml" in PRETTIER_FILE_PATTERNS).is_true()
    assert_that("*.yml" in PRETTIER_FILE_PATTERNS).is_true()
