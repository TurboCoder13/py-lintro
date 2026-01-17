"""Unit tests for gitleaks parser edge cases."""

from __future__ import annotations

import json

from assertpy import assert_that

from lintro.parsers.gitleaks.gitleaks_parser import parse_gitleaks_output


def test_parse_gitleaks_empty_array() -> None:
    """Empty array should return no issues."""
    issues = parse_gitleaks_output(output="[]")
    assert_that(issues).is_equal_to([])


def test_parse_gitleaks_empty_string() -> None:
    """Empty string should return no issues."""
    issues = parse_gitleaks_output(output="")
    assert_that(issues).is_equal_to([])


def test_parse_gitleaks_none_input() -> None:
    """None input should return no issues."""
    issues = parse_gitleaks_output(output=None)
    assert_that(issues).is_equal_to([])


def test_parse_gitleaks_whitespace_only() -> None:
    """Whitespace-only input should return no issues."""
    issues = parse_gitleaks_output(output="   \n\t  ")
    assert_that(issues).is_equal_to([])


def test_parse_gitleaks_invalid_json() -> None:
    """Invalid JSON should return empty list and log warning."""
    issues = parse_gitleaks_output(output="not valid json")
    assert_that(issues).is_equal_to([])


def test_parse_gitleaks_non_array_json() -> None:
    """Non-array JSON should return empty list."""
    issues = parse_gitleaks_output(output='{"not": "an array"}')
    assert_that(issues).is_equal_to([])


def test_parse_gitleaks_handles_malformed_finding_gracefully() -> None:
    """Malformed findings should be skipped."""
    sample_output = json.dumps(
        [
            None,
            42,
            {"File": "", "StartLine": 10},  # Empty file
            {"StartLine": 10},  # Missing File
            {
                "File": "valid.py",
                "StartLine": 5,
                "RuleID": "test-rule",
                "Description": "Valid finding",
            },
        ],
    )

    issues = parse_gitleaks_output(output=sample_output)

    # Only the last valid finding should be parsed
    assert_that(len(issues)).is_equal_to(1)
    assert_that(issues[0].file).is_equal_to("valid.py")
