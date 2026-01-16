"""Unit tests for shellcheck parser."""

from __future__ import annotations

import json

import pytest
from assertpy import assert_that

from lintro.parsers.shellcheck.shellcheck_parser import parse_shellcheck_output

# =============================================================================
# Empty/Invalid input tests
# =============================================================================


@pytest.mark.parametrize(
    "output",
    [
        None,
        "",
        "   \n  \n   ",
    ],
    ids=["none", "empty", "whitespace_only"],
)
def test_parse_shellcheck_output_returns_empty_for_no_content(
    output: str | None,
) -> None:
    """Parse empty, None, or whitespace-only output returns empty list.

    Args:
        output: The shellcheck output to parse.
    """
    result = parse_shellcheck_output(output=output)
    assert_that(result).is_empty()


def test_parse_shellcheck_output_returns_empty_for_invalid_json() -> None:
    """Parse invalid JSON returns empty list."""
    result = parse_shellcheck_output(output="not valid json")
    assert_that(result).is_empty()


def test_parse_shellcheck_output_returns_empty_for_non_array_json() -> None:
    """Parse JSON that is not an array returns empty list."""
    result = parse_shellcheck_output(output='{"key": "value"}')
    assert_that(result).is_empty()


def test_parse_shellcheck_output_empty_array() -> None:
    """Parse empty JSON array returns empty list."""
    result = parse_shellcheck_output(output="[]")
    assert_that(result).is_empty()


# =============================================================================
# Severity level tests
# =============================================================================


@pytest.mark.parametrize(
    "level,code",
    [
        ("error", 1072),
        ("warning", 2086),
        ("info", 2034),
        ("style", 2129),
    ],
)
def test_parse_shellcheck_output_severity_levels(level: str, code: int) -> None:
    """Parse issues with different severity levels.

    Args:
        level: The expected severity level.
        code: The expected error code.
    """
    data = [
        {
            "file": "script.sh",
            "line": 10,
            "column": 5,
            "level": level,
            "code": code,
            "message": "Test message",
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)
    assert_that(result).is_length(1)
    assert_that(result[0].level).is_equal_to(level)
    assert_that(result[0].code).is_equal_to(f"SC{code}")


# =============================================================================
# Field extraction tests
# =============================================================================


def test_parse_shellcheck_output_extracts_all_fields() -> None:
    """Parse issue extracts all fields correctly."""
    data = [
        {
            "file": "script.sh",
            "line": 10,
            "endLine": 12,
            "column": 5,
            "endColumn": 15,
            "level": "warning",
            "code": 2086,
            "message": "Double quote to prevent globbing and word splitting.",
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    issue = result[0]
    assert_that(issue.file).is_equal_to("script.sh")
    assert_that(issue.line).is_equal_to(10)
    assert_that(issue.end_line).is_equal_to(12)
    assert_that(issue.column).is_equal_to(5)
    assert_that(issue.end_column).is_equal_to(15)
    assert_that(issue.level).is_equal_to("warning")
    assert_that(issue.code).is_equal_to("SC2086")
    assert_that(issue.message).is_equal_to(
        "Double quote to prevent globbing and word splitting.",
    )


def test_parse_shellcheck_output_handles_missing_optional_fields() -> None:
    """Parse issue with missing optional fields uses defaults."""
    data = [
        {
            "file": "script.sh",
            "line": 10,
            "column": 5,
            "level": "warning",
            "code": 2086,
            "message": "Test message",
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].end_line).is_equal_to(0)
    assert_that(result[0].end_column).is_equal_to(0)


def test_parse_shellcheck_output_code_as_string() -> None:
    """Parse handles code as string (edge case)."""
    data = [
        {
            "file": "script.sh",
            "line": 10,
            "column": 5,
            "level": "warning",
            "code": "SC2086",
            "message": "Test message",
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].code).is_equal_to("SC2086")


# =============================================================================
# Multiple issues tests
# =============================================================================


def test_parse_shellcheck_output_multiple_issues() -> None:
    """Parse multiple issues."""
    data = [
        {
            "file": "script.sh",
            "line": 5,
            "column": 1,
            "level": "error",
            "code": 1072,
            "message": "Error message",
        },
        {
            "file": "script.sh",
            "line": 10,
            "column": 5,
            "level": "warning",
            "code": 2086,
            "message": "Warning message",
        },
        {
            "file": "other.sh",
            "line": 3,
            "column": 10,
            "level": "info",
            "code": 2034,
            "message": "Info message",
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(3)
    assert_that(result[0].line).is_equal_to(5)
    assert_that(result[1].line).is_equal_to(10)
    assert_that(result[2].line).is_equal_to(3)
    assert_that(result[2].file).is_equal_to("other.sh")


def test_parse_shellcheck_output_skips_non_dict_items() -> None:
    """Parse skips non-dictionary items in array."""
    data = [
        {
            "file": "script.sh",
            "line": 5,
            "column": 1,
            "level": "error",
            "code": 1072,
            "message": "Valid issue",
        },
        "not a dict",
        123,
        None,
        {
            "file": "script.sh",
            "line": 10,
            "column": 5,
            "level": "warning",
            "code": 2086,
            "message": "Another valid issue",
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(2)


# =============================================================================
# Edge case tests
# =============================================================================


def test_parse_shellcheck_output_unicode_in_message() -> None:
    """Handle Unicode characters in error messages."""
    data = [
        {
            "file": "script.sh",
            "line": 10,
            "column": 5,
            "level": "warning",
            "code": 2086,
            "message": "Mensagem com acentos: caf\u00e9",
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].message).contains("caf\u00e9")


def test_parse_shellcheck_output_file_with_path() -> None:
    """Parse file with directory path."""
    data = [
        {
            "file": "scripts/deploy/prod.sh",
            "line": 10,
            "column": 5,
            "level": "warning",
            "code": 2086,
            "message": "Test message",
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("scripts/deploy/prod.sh")


def test_parse_shellcheck_output_very_long_message() -> None:
    """Handle extremely long error messages."""
    long_text = "x" * 5000
    data = [
        {
            "file": "script.sh",
            "line": 10,
            "column": 5,
            "level": "warning",
            "code": 2086,
            "message": long_text,
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(len(result[0].message)).is_equal_to(5000)


def test_parse_shellcheck_output_very_large_line_number() -> None:
    """Handle very large line numbers."""
    data = [
        {
            "file": "script.sh",
            "line": 999999,
            "column": 5,
            "level": "warning",
            "code": 2086,
            "message": "Error on large line",
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].line).is_equal_to(999999)


def test_parse_shellcheck_output_special_chars_in_message() -> None:
    """Handle special characters in error messages."""
    data = [
        {
            "file": "script.sh",
            "line": 10,
            "column": 5,
            "level": "warning",
            "code": 2086,
            "message": 'Use "$var" instead of $var for safety.',
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].message).contains('"$var"')


def test_parse_shellcheck_output_deeply_nested_path() -> None:
    """Handle deeply nested file paths."""
    deep_path = "a/b/c/d/e/f/g/h/i/j/script.sh"
    data = [
        {
            "file": deep_path,
            "line": 10,
            "column": 5,
            "level": "warning",
            "code": 2086,
            "message": "Test message",
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to(deep_path)


def test_parse_shellcheck_output_missing_required_fields_uses_defaults() -> None:
    """Parse handles missing fields with defaults."""
    data = [
        {
            "level": "warning",
            "code": 2086,
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("")
    assert_that(result[0].line).is_equal_to(0)
    assert_that(result[0].column).is_equal_to(0)
    assert_that(result[0].message).is_equal_to("")


# =============================================================================
# Display row tests
# =============================================================================


def test_shellcheck_issue_to_display_row() -> None:
    """Test ShellcheckIssue to_display_row method."""
    data = [
        {
            "file": "script.sh",
            "line": 10,
            "column": 5,
            "level": "warning",
            "code": 2086,
            "message": "Test message",
        },
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    display_row = result[0].to_display_row()
    assert_that(display_row["file"]).is_equal_to("script.sh")
    assert_that(display_row["line"]).is_equal_to("10")
    assert_that(display_row["column"]).is_equal_to("5")
    assert_that(display_row["code"]).is_equal_to("SC2086")
    assert_that(display_row["message"]).is_equal_to("Test message")
    assert_that(display_row["severity"]).is_equal_to("warning")
