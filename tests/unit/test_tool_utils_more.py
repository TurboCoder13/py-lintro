"""Additional tests for tool_utils formatting and walking behavior."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.ruff.ruff_issue import RuffFormatIssue, RuffIssue
from lintro.utils.tool_utils import format_tool_output, walk_files_with_excludes


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
