"""Unit tests for darglint parser."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.parsers.darglint.darglint_parser import parse_darglint_output


@pytest.mark.parametrize(
    "output",
    [
        "",
        "All files passed!\n",
    ],
    ids=["empty", "no_issues"],
)
def test_parse_darglint_output_returns_empty_for_no_issues(output: str) -> None:
    """Parse output with no issues returns empty list.

    Args:
        output: The darglint output to parse.
    """
    result = parse_darglint_output(output)
    assert_that(result).is_empty()


def test_parse_darglint_output_standard_format_with_function() -> None:
    """Parse standard format: filename:function:line: CODE message."""
    output = "src/main.py:my_func:10: DAR101 Missing docstring"
    result = parse_darglint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("src/main.py")
    assert_that(result[0].line).is_equal_to(10)
    assert_that(result[0].code).is_equal_to("DAR101")
    assert_that(result[0].message).is_equal_to("Missing docstring")


def test_parse_darglint_output_standard_format_with_colon() -> None:
    """Parse format with colon after code: filename:function:line: CODE: message."""
    output = "src/main.py:my_func:10: DAR101: Missing docstring"
    result = parse_darglint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].code).is_equal_to("DAR101")
    assert_that(result[0].message).is_equal_to("Missing docstring")


def test_parse_darglint_output_module_level_format() -> None:
    """Parse module-level format: filename:line: CODE message."""
    output = "src/main.py:5: DAR001 Module missing docstring"
    result = parse_darglint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("src/main.py")
    assert_that(result[0].line).is_equal_to(5)
    assert_that(result[0].code).is_equal_to("DAR001")


def test_parse_darglint_output_multiple_issues() -> None:
    """Parse output with multiple issues."""
    output = """src/a.py:func_a:10: DAR101 Missing parameter
src/b.py:func_b:20: DAR102 Missing return"""
    result = parse_darglint_output(output)
    assert_that(result).is_length(2)
    assert_that(result[0].file).is_equal_to("src/a.py")
    assert_that(result[1].file).is_equal_to("src/b.py")


@pytest.mark.parametrize(
    "output,expected_contains",
    [
        (
            "src/main.py:func:10: DAR101 Missing parameter\n    parameter_name",
            "parameter_name",
        ),
        (
            "src/main.py:func:10: DAR101 Missing parameter\n: extra_info",
            "extra_info",
        ),
    ],
    ids=["continuation_indent", "continuation_colon"],
)
def test_parse_darglint_output_multiline_message(
    output: str,
    expected_contains: str,
) -> None:
    """Parse issue with multiline/continuation message.

    Args:
        output: The darglint output to parse.
        expected_contains: String that should be contained in the parsed message.
    """
    result = parse_darglint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].message).contains(expected_contains)


def test_parse_darglint_output_mixed_valid_and_invalid_lines() -> None:
    """Parse output with mix of valid and non-matching lines."""
    output = """Some header text
src/main.py:func:10: DAR101 Missing parameter
Random log line
src/other.py:func2:20: DAR102 Missing return"""
    result = parse_darglint_output(output)
    assert_that(result).is_length(2)


def test_parse_darglint_output_complex_code_format() -> None:
    """Parse issue with complex code like DARXXX."""
    output = "src/main.py:func:10: DARXXX123 Some error"
    result = parse_darglint_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].code).is_equal_to("DARXXX123")
