from __future__ import annotations

from assertpy import assert_that

from lintro.formatters.tools.black_formatter import (
    BlackTableDescriptor,
    format_black_issues,
)
from lintro.parsers.black.black_issue import BlackIssue


def test_black_table_descriptor_columns_and_rows():
    desc = BlackTableDescriptor()
    assert_that(desc.get_columns()).is_equal_to(["File", "Message"])
    issues = [
        BlackIssue(file="src/a.py", message="Would reformat file"),
        BlackIssue(file="b.py", message="Reformatted file"),
    ]
    rows = desc.get_rows(issues)
    assert_that(rows[0][0].endswith("src/a.py")).is_true()
    assert_that(rows[0][1]).contains("reformat")


def test_format_black_issues_all_styles():
    issues = [
        BlackIssue(file="a.py", message="Would reformat file"),
        BlackIssue(file="b.py", message="Reformatted file"),
    ]
    for style in ["grid", "markdown", "html", "json", "csv", "plain"]:
        out = format_black_issues(issues=issues, format=style)
        assert_that(isinstance(out, str)).is_true()
        assert_that(len(out) > 0).is_true()


def test_format_black_issues_empty():
    out = format_black_issues(issues=[], format="grid")
    # Grid formatter returns an empty string when no rows
    assert_that(isinstance(out, str)).is_true()
