"""Unit tests for GitleaksIssue model."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.gitleaks.gitleaks_issue import GitleaksIssue


def test_gitleaks_issue_display_row() -> None:
    """GitleaksIssue should produce correct display row."""
    issue = GitleaksIssue(  # nosec B106 - test data for secret detection
        file="config.py",
        line=10,
        column=5,
        rule_id="aws-access-key-id",
        description="AWS Access Key",
        secret="AKIAEXAMPLE",
    )

    row = issue.to_display_row()

    assert_that(row["file"]).is_equal_to("config.py")
    assert_that(row["line"]).is_equal_to("10")
    assert_that(row["column"]).is_equal_to("5")
    assert_that(row["code"]).is_equal_to("aws-access-key-id")
    assert_that(row["message"]).contains("AWS Access Key")
    assert_that(row["message"]).contains("[REDACTED]")


def test_gitleaks_issue_message_without_secret() -> None:
    """GitleaksIssue message should not show REDACTED when no secret."""
    issue = GitleaksIssue(  # nosec B106 - test data for secret detection
        file="test.py",
        line=1,
        column=1,
        rule_id="test-rule",
        description="Test Description",
        secret="",
    )

    assert_that(issue.message).is_equal_to("[test-rule] Test Description")
    assert_that(issue.message).does_not_contain("REDACTED")
