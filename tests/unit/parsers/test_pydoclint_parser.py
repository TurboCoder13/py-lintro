"""Unit tests for pydoclint parser."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.pydoclint.pydoclint_parser import parse_pydoclint_output


def test_parse_pydoclint_output_empty() -> None:
    """Handle empty and None output."""
    assert_that(parse_pydoclint_output(None)).is_empty()
    assert_that(parse_pydoclint_output("")).is_empty()
    assert_that(parse_pydoclint_output("   \n\n  ")).is_empty()


def test_parse_pydoclint_output_single_file_single_issue() -> None:
    """Parse single file with single issue."""
    output = """/path/to/file.py
    10: DOC101: Function `foo` has 1 argument(s) missing"""
    issues = parse_pydoclint_output(output)
    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("/path/to/file.py")
    assert_that(issues[0].line).is_equal_to(10)
    assert_that(issues[0].code).is_equal_to("DOC101")
    assert_that(issues[0].message).contains("argument(s)")
    # pydoclint doesn't provide column info
    assert_that(issues[0].column).is_equal_to(0)


def test_parse_pydoclint_output_single_file_multiple_issues() -> None:
    """Parse single file with multiple issues."""
    output = """/path/to/file.py
    10: DOC101: Missing argument
    15: DOC102: Missing return"""
    issues = parse_pydoclint_output(output)
    assert_that(issues).is_length(2)
    assert_that(issues[0].line).is_equal_to(10)
    assert_that(issues[1].line).is_equal_to(15)


def test_parse_pydoclint_output_multiple_files() -> None:
    """Parse multiple files with issues."""
    output = """/path/to/file1.py
    10: DOC101: Issue in file1
/path/to/file2.py
    20: DOC102: Issue in file2"""
    issues = parse_pydoclint_output(output)
    assert_that(issues).is_length(2)
    assert_that(issues[0].file).is_equal_to("/path/to/file1.py")
    assert_that(issues[1].file).is_equal_to("/path/to/file2.py")


def test_parse_pydoclint_output_ansi_codes_stripped() -> None:
    """Strip ANSI escape codes from output for consistent CI/local parsing."""
    # Output with ANSI color codes (common in CI environments)
    output = """\x1b[1m/path/to/file.py\x1b[0m
    \x1b[31m10: DOC101: Function `foo` has 1 argument(s) missing\x1b[0m"""
    issues = parse_pydoclint_output(output)
    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("/path/to/file.py")
    assert_that(issues[0].code).is_equal_to("DOC101")
