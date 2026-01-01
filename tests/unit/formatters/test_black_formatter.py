"""Tests for Black formatter table and output rendering."""

from __future__ import annotations

from assertpy import assert_that

from lintro.enums.output_format import OutputFormat
from lintro.formatters.tools.black_formatter import (
    BlackTableDescriptor,
    format_black_issues,
)
from lintro.parsers.black.black_issue import BlackIssue


def test_black_table_descriptor_columns_and_rows() -> None:
    """Ensure columns and rows render expected values for issues."""
    desc = BlackTableDescriptor()
    assert_that(desc.get_columns()).is_equal_to(["File", "Message"])
    issues = [
        BlackIssue(file="src/a.py", message="Would reformat file"),
        BlackIssue(file="b.py", message="Reformatted file"),
    ]
    rows = desc.get_rows(issues)
    assert_that(rows[0][0].endswith("src/a.py")).is_true()
    assert_that(rows[0][1]).contains("reformat")


def test_format_black_issues_all_styles() -> None:
    """Ensure all styles return a non-empty string for issues list."""
    issues = [
        BlackIssue(file="a.py", message="Would reformat file"),
        BlackIssue(file="b.py", message="Reformatted file"),
    ]
    output_formats = [
        OutputFormat.GRID,
        OutputFormat.MARKDOWN,
        OutputFormat.HTML,
        OutputFormat.JSON,
        OutputFormat.CSV,
        OutputFormat.PLAIN,
    ]
    for style in output_formats:
        out = format_black_issues(issues=issues, format=style)
        assert_that(isinstance(out, str)).is_true()
        assert_that(len(out) > 0).is_true()


def test_format_black_issues_empty() -> None:
    """Ensure empty issues still produce a valid string output."""
    out = format_black_issues(issues=[], format=OutputFormat.GRID)
    # Grid formatter returns an empty string when no rows
    assert_that(isinstance(out, str)).is_true()
