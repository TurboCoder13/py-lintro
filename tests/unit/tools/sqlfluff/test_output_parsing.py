"""Unit tests for sqlfluff output parsing."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.sqlfluff.sqlfluff_parser import parse_sqlfluff_output


def test_parse_sqlfluff_output_single_issue() -> None:
    """Parse single issue from sqlfluff output."""
    output = """[
        {
            "filepath": "test.sql",
            "violations": [
                {
                    "start_line_no": 1,
                    "start_line_pos": 1,
                    "code": "L010",
                    "description": "Keywords must be upper case.",
                    "name": "capitalisation.keywords"
                }
            ]
        }
    ]"""
    issues = parse_sqlfluff_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).is_equal_to("test.sql")
    assert_that(issues[0].line).is_equal_to(1)
    assert_that(issues[0].code).is_equal_to("L010")
    assert_that(issues[0].message).contains("Keywords must be upper case")


def test_parse_sqlfluff_output_multiple_issues() -> None:
    """Parse multiple issues from sqlfluff output."""
    output = """[
        {
            "filepath": "test.sql",
            "violations": [
                {
                    "start_line_no": 1,
                    "start_line_pos": 1,
                    "code": "L010",
                    "description": "Keywords must be upper case."
                },
                {
                    "start_line_no": 2,
                    "start_line_pos": 5,
                    "code": "L011",
                    "description": "Implicit aliasing of columns."
                }
            ]
        }
    ]"""
    issues = parse_sqlfluff_output(output)

    assert_that(issues).is_length(2)
    assert_that(issues[0].code).is_equal_to("L010")
    assert_that(issues[1].code).is_equal_to("L011")


def test_parse_sqlfluff_output_multiple_files() -> None:
    """Parse issues from multiple files."""
    output = """[
        {
            "filepath": "test1.sql",
            "violations": [
                {
                    "start_line_no": 1,
                    "start_line_pos": 1,
                    "code": "L010",
                    "description": "Keywords must be upper case."
                }
            ]
        },
        {
            "filepath": "test2.sql",
            "violations": [
                {
                    "start_line_no": 3,
                    "start_line_pos": 10,
                    "code": "L014",
                    "description": "Inconsistent capitalisation."
                }
            ]
        }
    ]"""
    issues = parse_sqlfluff_output(output)

    assert_that(issues).is_length(2)
    assert_that(issues[0].file).is_equal_to("test1.sql")
    assert_that(issues[1].file).is_equal_to("test2.sql")


def test_parse_sqlfluff_output_empty() -> None:
    """Parse empty output returns empty list."""
    issues = parse_sqlfluff_output("")

    assert_that(issues).is_empty()


def test_parse_sqlfluff_output_empty_array() -> None:
    """Parse empty array returns empty list."""
    issues = parse_sqlfluff_output("[]")

    assert_that(issues).is_empty()


def test_parse_sqlfluff_output_no_violations() -> None:
    """Parse output with no violations returns empty list."""
    output = """[
        {
            "filepath": "test.sql",
            "violations": []
        }
    ]"""
    issues = parse_sqlfluff_output(output)

    assert_that(issues).is_empty()


def test_parse_sqlfluff_output_invalid_json() -> None:
    """Parse invalid JSON returns empty list."""
    issues = parse_sqlfluff_output("not valid json")

    assert_that(issues).is_empty()
