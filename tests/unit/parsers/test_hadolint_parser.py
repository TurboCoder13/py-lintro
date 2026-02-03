"""Unit tests for hadolint parser."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.parsers.hadolint.hadolint_parser import parse_hadolint_output


@pytest.mark.parametrize(
    "output",
    [
        "",
        "   \n  \n   ",
    ],
    ids=["empty", "whitespace_only"],
)
def test_parse_hadolint_output_returns_empty_for_no_content(output: str) -> None:
    """Parse empty or whitespace-only output returns empty list.

    Args:
        output: The hadolint output to parse.
    """
    result = parse_hadolint_output(output)
    assert_that(result).is_empty()


@pytest.mark.parametrize(
    "level,code,output_line",
    [
        ("error", "DL3006", "Dockerfile:1 DL3006 error: Always tag the version"),
        ("warning", "DL3009", "Dockerfile:3 DL3009 warning: Delete apt-get lists"),
        ("info", "DL3015", "Dockerfile:5 DL3015 info: Avoid additional packages"),
        ("style", "DL3000", "Dockerfile:10 DL3000 style: Use absolute WORKDIR"),
    ],
)
def test_parse_hadolint_output_severity_levels(
    level: str,
    code: str,
    output_line: str,
) -> None:
    """Parse issues with different severity levels.

    Args:
        level: The expected severity level.
        code: The expected error code.
        output_line: The hadolint output line to parse.
    """
    result = parse_hadolint_output(output_line)
    assert_that(result).is_length(1)
    assert_that(result[0].level).is_equal_to(level)
    assert_that(result[0].code).is_equal_to(code)


def test_parse_hadolint_output_extracts_all_fields() -> None:
    """Parse error-level issue extracts all fields correctly."""
    output = "Dockerfile:1 DL3006 error: Always tag the version of an image explicitly"
    result = parse_hadolint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("Dockerfile")
    assert_that(result[0].line).is_equal_to(1)
    assert_that(result[0].code).is_equal_to("DL3006")
    assert_that(result[0].level).is_equal_to("error")
    assert_that(result[0].message).is_equal_to(
        "Always tag the version of an image explicitly",
    )


def test_parse_hadolint_output_multiple_issues() -> None:
    """Parse multiple issues."""
    output = """Dockerfile:1 DL3006 error: Always tag the version
Dockerfile:3 DL3009 warning: Delete apt-get lists
Dockerfile:5 DL3015 info: Avoid additional packages"""
    result = parse_hadolint_output(output)
    assert_that(result).is_length(3)
    assert_that(result[0].line).is_equal_to(1)
    assert_that(result[1].line).is_equal_to(3)
    assert_that(result[2].line).is_equal_to(5)


def test_parse_hadolint_output_non_matching_lines_ignored() -> None:
    """Non-matching lines are ignored."""
    output = """Some header text
Dockerfile:1 DL3006 error: Tag the version
Other random output"""
    result = parse_hadolint_output(output)
    assert_that(result).is_length(1)


def test_parse_hadolint_output_column_is_zero() -> None:
    """Column is always 0 (hadolint doesn't provide it)."""
    output = "Dockerfile:1 DL3006 error: Some error"
    result = parse_hadolint_output(output)
    assert_that(result[0].column).is_equal_to(0)


def test_parse_hadolint_output_file_with_path() -> None:
    """Parse file with directory path."""
    output = "docker/prod/Dockerfile:10 DL3006 error: Tag the version"
    result = parse_hadolint_output(output)
    assert_that(result[0].file).is_equal_to("docker/prod/Dockerfile")


def test_parse_hadolint_output_blank_lines_between_issues() -> None:
    """Handle blank lines between issues."""
    output = """Dockerfile:1 DL3006 error: Error one

Dockerfile:5 DL3009 warning: Warning one"""
    result = parse_hadolint_output(output)
    assert_that(result).is_length(2)


# =============================================================================
# Edge case tests
# =============================================================================


def test_parse_hadolint_output_unicode_in_message() -> None:
    """Handle Unicode characters in error messages."""
    output = "Dockerfile:1 DL3006 error: Não use versões implícitas"
    result = parse_hadolint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].message).contains("Não")


def test_parse_hadolint_output_file_path_with_spaces() -> None:
    """Handle file paths with spaces (if quoted by tool)."""
    output = "my project/Dockerfile:1 DL3006 error: Tag version"
    result = parse_hadolint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).contains("my project")


def test_parse_hadolint_output_very_long_message() -> None:
    """Handle extremely long error messages."""
    long_text = "x" * 5000
    output = f"Dockerfile:1 DL3006 error: {long_text}"
    result = parse_hadolint_output(output)
    assert_that(result).is_length(1)
    assert_that(len(result[0].message)).is_equal_to(5000)


def test_parse_hadolint_output_very_large_line_number() -> None:
    """Handle very large line numbers."""
    output = "Dockerfile:999999 DL3006 error: Error on large line"
    result = parse_hadolint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].line).is_equal_to(999999)


def test_parse_hadolint_output_special_chars_in_message() -> None:
    """Handle special characters in error messages."""
    output = 'Dockerfile:1 DL3006 error: Use "quotes" and <brackets>'
    result = parse_hadolint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].message).contains("quotes")
    assert_that(result[0].message).contains("<brackets>")


def test_parse_hadolint_output_colon_in_message() -> None:
    """Handle colons in error messages (common in Docker contexts)."""
    output = "Dockerfile:1 DL3006 error: FROM should use image:tag format"
    result = parse_hadolint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].message).contains("image:tag")


def test_parse_hadolint_output_deeply_nested_path() -> None:
    """Handle deeply nested file paths."""
    deep_path = "a/b/c/d/e/f/g/h/i/j/Dockerfile"
    output = f"{deep_path}:1 DL3006 error: Tag version"
    result = parse_hadolint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to(deep_path)


def test_parse_hadolint_output_ansi_codes_stripped() -> None:
    """Strip ANSI escape codes from output for consistent CI/local parsing."""
    # Output with ANSI color codes (common in CI environments)
    output = "\x1b[31mDockerfile:1 DL3006 error: Always tag the version\x1b[0m"
    result = parse_hadolint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("Dockerfile")
    assert_that(result[0].code).is_equal_to("DL3006")
