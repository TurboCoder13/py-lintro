"""Tests for pydoclint issue model."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.pydoclint.pydoclint_issue import PydoclintIssue


def test_issue_defaults() -> None:
    """Issue has correct default values."""
    issue = PydoclintIssue()

    assert_that(issue.file).is_equal_to("")
    assert_that(issue.line).is_equal_to(0)
    assert_that(issue.column).is_equal_to(0)
    assert_that(issue.code).is_equal_to("")
    assert_that(issue.message).is_equal_to("")


def test_issue_with_values() -> None:
    """Issue stores values correctly."""
    issue = PydoclintIssue(
        file="test.py",
        line=10,
        column=5,
        code="DOC101",
        message="Test message",
    )

    assert_that(issue.file).is_equal_to("test.py")
    assert_that(issue.line).is_equal_to(10)
    assert_that(issue.column).is_equal_to(5)
    assert_that(issue.code).is_equal_to("DOC101")
    assert_that(issue.message).is_equal_to("Test message")


def test_to_display_row() -> None:
    """Issue converts to display row correctly."""
    issue = PydoclintIssue(
        file="test.py",
        line=10,
        column=5,
        code="DOC101",
        message="Test message",
    )

    row = issue.to_display_row()

    assert_that(row["file"]).is_equal_to("test.py")
    assert_that(row["line"]).is_equal_to("10")
    assert_that(row["column"]).is_equal_to("5")
    assert_that(row["code"]).is_equal_to("DOC101")
    assert_that(row["message"]).is_equal_to("Test message")


def test_to_display_row_with_zero_line() -> None:
    """Issue with zero line displays dash."""
    issue = PydoclintIssue(
        file="test.py",
        line=0,
        column=0,
        code="DOC101",
        message="Test message",
    )

    row = issue.to_display_row()

    assert_that(row["line"]).is_equal_to("-")
    assert_that(row["column"]).is_equal_to("-")
