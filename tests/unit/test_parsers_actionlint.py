"""Unit tests for the Actionlint output parser.

These tests validate that the parser handles empty output and typical
``file:line:col: level: message [CODE]`` lines, producing structured issues.
"""

from assertpy import assert_that

from lintro.parsers.actionlint.actionlint_parser import parse_actionlint_output


def test_parse_actionlint_empty() -> None:
    """Return an empty list for empty parser input."""
    assert_that(parse_actionlint_output("")).is_equal_to([])


def test_parse_actionlint_lines() -> None:
    """Parse typical actionlint lines and produce structured issues."""
    out = (
        "workflow.yml:10:5: error: unexpected key [AL100]\n"
        "workflow.yml:12:3: warning: something minor"
    )
    issues = parse_actionlint_output(out)
    assert_that(len(issues)).is_equal_to(2)
    i0 = issues[0]
    assert_that(i0.file).is_equal_to("workflow.yml")
    assert_that(i0.line).is_equal_to(10)
    assert_that(i0.column).is_equal_to(5)
    assert_that(i0.level).is_equal_to("error")
    assert_that(i0.code).is_equal_to("AL100")
    assert_that(i0.message).contains("unexpected key")
