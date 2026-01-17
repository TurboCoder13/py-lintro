"""Tests for shellcheck parser handling multiple issues."""

from __future__ import annotations

import json

from assertpy import assert_that

from lintro.parsers.shellcheck.shellcheck_parser import parse_shellcheck_output

from .conftest import make_issue, make_shellcheck_output


def test_parse_multiple_issues() -> None:
    """Parse multiple issues."""
    output = make_shellcheck_output(
        [
            make_issue(
                file="script.sh",
                line=5,
                column=1,
                level="error",
                code=1072,
                message="Error message",
            ),
            make_issue(
                file="script.sh",
                line=10,
                column=5,
                level="warning",
                code=2086,
                message="Warning message",
            ),
            make_issue(
                file="other.sh",
                line=3,
                column=10,
                level="info",
                code=2034,
                message="Info message",
            ),
        ]
    )
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(3)
    assert_that(result[0].line).is_equal_to(5)
    assert_that(result[1].line).is_equal_to(10)
    assert_that(result[2].line).is_equal_to(3)
    assert_that(result[2].file).is_equal_to("other.sh")


def test_parse_skips_non_dict_items() -> None:
    """Parse skips non-dictionary items in array."""
    data = [
        make_issue(line=5, level="error", code=1072, message="Valid issue"),
        "not a dict",
        123,
        None,
        make_issue(line=10, level="warning", code=2086, message="Another valid issue"),
    ]
    output = json.dumps(data)
    result = parse_shellcheck_output(output=output)

    assert_that(result).is_length(2)
