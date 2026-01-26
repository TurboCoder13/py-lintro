"""Tests for pydoclint parser field extraction."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.parsers.pydoclint.pydoclint_parser import parse_pydoclint_output

from .conftest import make_issue, make_pydoclint_output


@pytest.mark.parametrize(
    ("code", "message"),
    [
        ("DOC101", "Function `foo` has 1 argument(s) in signature: ['x']"),
        ("DOC102", "Function `foo` has 2 argument(s) in docstring"),
        ("DOC103", "Argument `y` does not exist in `foo`'s signature"),
        ("DOC201", "Function `foo` does not have a return section"),
        ("DOC202", "Function `foo` has return type, but no return section"),
        ("DOC301", "Function `foo` does not have a Raises section"),
        ("DOC401", "Class `Foo` has 1 attribute(s) in docstring"),
        ("DOC501", "Function `foo` has raises section but no raises in body"),
        ("DOC502", "Function `foo` raises ValueError but does not document it"),
    ],
    ids=[
        "DOC101_missing_arg",
        "DOC102_extra_arg",
        "DOC103_nonexistent_arg",
        "DOC201_no_return_section",
        "DOC202_return_type_no_section",
        "DOC301_no_raises_section",
        "DOC401_class_attributes",
        "DOC501_raises_section_no_raises",
        "DOC502_undocumented_raises",
    ],
)
def test_parse_doc_codes(code: str, message: str) -> None:
    """Parse issues with different DOC codes.

    Args:
        code: The expected DOC code.
        message: The expected message.
    """
    output = make_pydoclint_output([make_issue(code=code, message=message)])
    result = parse_pydoclint_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].code).is_equal_to(code)
    assert_that(result[0].message).is_equal_to(message)


def test_parse_extracts_all_fields() -> None:
    """Parse issue extracts all fields correctly.

    Note: pydoclint doesn't report column information, so column is always 0.
    """
    output = make_pydoclint_output(
        [
            make_issue(
                file="src/module.py",
                line=42,
                column=0,  # pydoclint doesn't report columns
                code="DOC101",
                message="Function `calculate` has 2 argument(s) in signature",
            ),
        ],
    )
    result = parse_pydoclint_output(output=output)

    assert_that(result).is_length(1)
    issue = result[0]
    assert_that(issue.file).is_equal_to("src/module.py")
    assert_that(issue.line).is_equal_to(42)
    assert_that(issue.column).is_equal_to(0)  # pydoclint doesn't report columns
    assert_that(issue.code).is_equal_to("DOC101")
    assert_that(issue.message).is_equal_to(
        "Function `calculate` has 2 argument(s) in signature",
    )


def test_parse_multiple_issues() -> None:
    """Parse multiple issues from output."""
    output = make_pydoclint_output(
        [
            make_issue(file="test1.py", line=10, code="DOC101"),
            make_issue(file="test2.py", line=20, code="DOC201"),
            make_issue(file="test3.py", line=30, code="DOC301"),
        ],
    )
    result = parse_pydoclint_output(output=output)

    assert_that(result).is_length(3)
    assert_that(result[0].file).is_equal_to("test1.py")
    assert_that(result[0].code).is_equal_to("DOC101")
    assert_that(result[1].file).is_equal_to("test2.py")
    assert_that(result[1].code).is_equal_to("DOC201")
    assert_that(result[2].file).is_equal_to("test3.py")
    assert_that(result[2].code).is_equal_to("DOC301")


def test_parse_nested_path() -> None:
    """Parse issue with nested file path."""
    output = """src/utils/helpers/formatter.py
    100: DOC101: Test message"""
    result = parse_pydoclint_output(output=output)

    assert_that(result).is_length(1)
    assert_that(result[0].file).is_equal_to("src/utils/helpers/formatter.py")
    assert_that(result[0].line).is_equal_to(100)
    assert_that(result[0].column).is_equal_to(0)  # pydoclint doesn't report columns
