from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.ruff.ruff_issue import RuffFormatIssue, RuffIssue
from lintro.utils.tool_utils import format_tool_output


def test_format_tool_output_with_parsed_issues_and_fixable_sections(monkeypatch):
    import lintro.utils.tool_utils as tu

    def fake_tabulate(tabular_data, headers, tablefmt, stralign, disable_numparse):
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


def test_format_tool_output_parsing_fallbacks(monkeypatch):
    out = format_tool_output(
        tool_name="unknown",
        output="some raw output",
        group_by="auto",
        output_format="grid",
        issues=None,
    )
    assert_that(out).is_equal_to("some raw output")
