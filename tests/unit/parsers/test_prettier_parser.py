"""Unit tests for prettier parser."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.parsers.prettier.prettier_parser import parse_prettier_output


@pytest.mark.parametrize(
    "output",
    [
        "",
        "Checking formatting...\nAll matched files use Prettier code style!",
    ],
    ids=["empty", "no_issues"],
)
def test_parse_prettier_output_returns_empty_for_no_issues(output: str) -> None:
    """Parse output with no issues returns empty list.

    Args:
        output: The prettier output to parse.
    """
    result = parse_prettier_output(output)
    assert_that(result).is_empty()


def test_parse_prettier_output_single_file_issue() -> None:
    """Parse single file with formatting issue."""
    output = """Checking formatting...
[warn] src/main.js
[warn] Code style issues found in the above file. Run Prettier with --write to fix."""
    result = parse_prettier_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("src/main.js")
    assert_that(result[0].code).is_equal_to("FORMAT")
    assert_that(result[0].message).is_equal_to("Code style issues found")


def test_parse_prettier_output_multiple_file_issues() -> None:
    """Parse multiple files with formatting issues."""
    output = """Checking formatting...
[warn] src/a.js
[warn] src/b.ts
[warn] src/c.json
[warn] Code style issues found in the above files. Run Prettier with --write to fix."""
    result = parse_prettier_output(output)
    assert_that(result).is_length(3)
    assert_that(result[0].file).is_equal_to("src/a.js")
    assert_that(result[1].file).is_equal_to("src/b.ts")
    assert_that(result[2].file).is_equal_to("src/c.json")


def test_parse_prettier_output_ansi_escape_codes_stripped() -> None:
    """Strip ANSI escape codes from output."""
    output = "[\x1b[33mwarn\x1b[39m] src/file.js"
    result = parse_prettier_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("src/file.js")


def test_parse_prettier_output_ignores_code_style_message() -> None:
    """Ignore the 'Code style issues' summary line."""
    output = """[warn] src/file.js
[warn] Code style issues found in the above file. Run Prettier with --write to fix."""
    result = parse_prettier_output(output)
    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("src/file.js")


def test_parse_prettier_output_blank_lines_ignored() -> None:
    """Blank lines are ignored."""
    output = """[warn] src/a.js

[warn] src/b.js"""
    result = parse_prettier_output(output)
    assert_that(result).is_length(2)


def test_parse_prettier_output_default_line_and_column() -> None:
    """Default line and column are 1."""
    output = "[warn] src/file.js"
    result = parse_prettier_output(output)
    assert_that(result[0].line).is_equal_to(1)
    assert_that(result[0].column).is_equal_to(1)


def test_parse_prettier_output_non_warn_lines_ignored() -> None:
    """Lines not starting with [warn] are ignored."""
    output = """Checking formatting...
[info] Some info message
[warn] src/file.js
All done!"""
    result = parse_prettier_output(output)
    assert_that(result).is_length(1)
