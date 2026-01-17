"""Unit tests for gitleaks parser field-specific parsing."""

from __future__ import annotations

import json

from assertpy import assert_that

from lintro.parsers.gitleaks.gitleaks_parser import parse_gitleaks_output


def test_parse_gitleaks_git_history_fields() -> None:
    """Parser should handle git history fields from commit scanning."""
    sample_output = json.dumps(
        [
            {
                "Description": "API Key",
                "StartLine": 1,
                "EndLine": 1,
                "StartColumn": 1,
                "EndColumn": 30,
                "File": "secret.py",
                "Commit": "abc123def456",
                "Author": "John Doe",
                "Email": "john@example.com",
                "Date": "2024-01-15T10:30:00Z",
                "Message": "Add configuration",
                "RuleID": "generic-api-key",
                "Fingerprint": "secret.py:generic-api-key:1:abc123def456",
            },
        ],
    )

    issues = parse_gitleaks_output(output=sample_output)

    assert_that(len(issues)).is_equal_to(1)
    issue = issues[0]
    assert_that(issue.commit).is_equal_to("abc123def456")
    assert_that(issue.author).is_equal_to("John Doe")
    assert_that(issue.email).is_equal_to("john@example.com")
    assert_that(issue.date).is_equal_to("2024-01-15T10:30:00Z")
    assert_that(issue.commit_message).is_equal_to("Add configuration")


def test_gitleaks_entropy_parsing() -> None:
    """Parser should correctly handle entropy as float."""
    sample_output = json.dumps(
        [
            {
                "File": "test.py",
                "StartLine": 1,
                "Entropy": 4.25,
                "RuleID": "test",
            },
        ],
    )

    issues = parse_gitleaks_output(output=sample_output)

    assert_that(len(issues)).is_equal_to(1)
    assert_that(issues[0].entropy).is_equal_to(4.25)


def test_gitleaks_entropy_as_int() -> None:
    """Parser should handle entropy as integer."""
    sample_output = json.dumps(
        [
            {
                "File": "test.py",
                "StartLine": 1,
                "Entropy": 4,
                "RuleID": "test",
            },
        ],
    )

    issues = parse_gitleaks_output(output=sample_output)

    assert_that(len(issues)).is_equal_to(1)
    assert_that(issues[0].entropy).is_equal_to(4.0)


def test_gitleaks_tags_empty_list() -> None:
    """Parser should handle empty tags list."""
    sample_output = json.dumps(
        [
            {
                "File": "test.py",
                "StartLine": 1,
                "Tags": [],
                "RuleID": "test",
            },
        ],
    )

    issues = parse_gitleaks_output(output=sample_output)

    assert_that(len(issues)).is_equal_to(1)
    assert_that(issues[0].tags).is_equal_to([])


def test_gitleaks_tags_none() -> None:
    """Parser should handle missing tags field."""
    sample_output = json.dumps(
        [
            {
                "File": "test.py",
                "StartLine": 1,
                "RuleID": "test",
            },
        ],
    )

    issues = parse_gitleaks_output(output=sample_output)

    assert_that(len(issues)).is_equal_to(1)
    assert_that(issues[0].tags).is_equal_to([])
