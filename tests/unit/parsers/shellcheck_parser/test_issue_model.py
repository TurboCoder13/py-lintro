"""Tests for ShellcheckIssue model methods."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.shellcheck.shellcheck_parser import parse_shellcheck_output

from .conftest import make_issue, make_shellcheck_output


def test_to_display_row() -> None:
    """Test ShellcheckIssue to_display_row method."""
    output = make_shellcheck_output(
        [
            make_issue(
                file="script.sh",
                line=10,
                column=5,
                level="warning",
                code=2086,
                message="Test message",
            ),
        ],
    )
    result = parse_shellcheck_output(output=output)

    display_row = result[0].to_display_row()
    assert_that(display_row["file"]).is_equal_to("script.sh")
    assert_that(display_row["line"]).is_equal_to("10")
    assert_that(display_row["column"]).is_equal_to("5")
    assert_that(display_row["code"]).is_equal_to("SC2086")
    assert_that(display_row["message"]).is_equal_to("Test message")
    assert_that(display_row["severity"]).is_equal_to("WARNING")
