"""Unit tests for yamllint parser."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.parsers.yamllint.yamllint_parser import parse_yamllint_output


@pytest.mark.parametrize(
    "output",
    [
        "",
        "   \n  \n   ",
    ],
    ids=["empty", "whitespace_only"],
)
def test_parse_yamllint_output_returns_empty_for_no_content(output: str) -> None:
    """Parse empty or whitespace-only output returns empty list.

    Args:
        output: The yamllint output string to parse.
    """
    result = parse_yamllint_output(output)
    assert_that(result).is_empty()


@pytest.mark.parametrize(
    "level,output_line",
    [
        ("error", "config.yml:10:5: [error] trailing spaces (trailing-spaces)"),
        (
            "warning",
            'test.yml:3:1: [warning] missing document start "---" (document-start)',
        ),
    ],
)
def test_parse_yamllint_output_severity_levels(level: str, output_line: str) -> None:
    """Parse issues with different severity levels.

    Args:
        level: The expected severity level.
        output_line: The yamllint output line to parse.
    """
    result = parse_yamllint_output(output_line)
    assert_that(result).is_length(1)
    assert_that(result[0].level.value.lower()).is_equal_to(level)


def test_parse_yamllint_output_extracts_all_fields() -> None:
    """Parse error-level issue extracts all fields correctly."""
    output = "config.yml:10:5: [error] trailing spaces (trailing-spaces)"
    result = parse_yamllint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("config.yml")
    assert_that(result[0].line).is_equal_to(10)
    assert_that(result[0].column).is_equal_to(5)
    assert_that(result[0].message).is_equal_to("trailing spaces")
    assert_that(result[0].rule).is_equal_to("trailing-spaces")


def test_parse_yamllint_output_multiple_issues() -> None:
    """Parse multiple issues."""
    output = """config.yml:5:10: [error] trailing spaces (trailing-spaces)
config.yml:10:1: [warning] missing document start (document-start)
other.yml:3:15: [error] line too long (line-length)"""
    result = parse_yamllint_output(output)
    assert_that(result).is_length(3)
    assert_that(result[0].file).is_equal_to("config.yml")
    assert_that(result[1].line).is_equal_to(10)
    assert_that(result[2].file).is_equal_to("other.yml")


def test_parse_yamllint_output_non_matching_lines_ignored() -> None:
    """Non-matching lines are ignored."""
    output = """Some header text
config.yml:5:10: [error] trailing spaces (trailing-spaces)
Other random output"""
    result = parse_yamllint_output(output)
    assert_that(result).is_length(1)


def test_parse_yamllint_output_issue_without_rule() -> None:
    """Parse issue without rule in parentheses."""
    output = "config.yml:5:10: [error] trailing spaces"
    result = parse_yamllint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].rule).is_none()


def test_parse_yamllint_output_complex_message() -> None:
    """Parse issue with complex message."""
    output = "test.yml:11:81: [error] line too long (149 > 80 characters) (line-length)"
    result = parse_yamllint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].message).contains("line too long")


def test_parse_yamllint_output_blank_lines_between_issues() -> None:
    """Handle blank lines between issues."""
    output = """config.yml:5:10: [error] error one (rule1)

config.yml:10:1: [warning] warning one (rule2)"""
    result = parse_yamllint_output(output)
    assert_that(result).is_length(2)
