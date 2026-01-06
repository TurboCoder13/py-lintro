"""Unit tests for mypy parser."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.mypy.mypy_parser import parse_mypy_output


def test_parse_mypy_json_array() -> None:
    """Parse standard mypy JSON array output."""
    output = (
        '[{"path":"app.py","line":3,"column":5,"endLine":3,"endColumn":10,'
        '"message":"Incompatible return value type","code":"return-value"}]'
    )
    issues = parse_mypy_output(output)

    assert_that(issues).is_length(1)
    issue = issues[0]
    assert_that(issue.file).ends_with("app.py")
    assert_that(issue.line).is_equal_to(3)
    assert_that(issue.column).is_equal_to(5)
    assert_that(issue.end_line).is_equal_to(3)
    assert_that(issue.end_column).is_equal_to(10)
    assert_that(issue.code).is_equal_to("return-value")


def test_parse_mypy_errors_object() -> None:
    """Parse mypy output wrapped in an errors object."""
    output = (
        "{"
        '"errors": ['
        '{"filename": "service.py", "line": 1, "column": 1, '
        '"message": "Name \\"x\\" is not defined", '
        '"code": {"code": "name-defined"}, "severity": "error"}'
        "]"
        "}"
    )

    issues = parse_mypy_output(output)
    assert_that(issues).is_length(1)
    issue = issues[0]
    assert_that(issue.file).ends_with("service.py")
    assert_that(issue.code).is_equal_to("name-defined")
    assert_that(issue.severity).is_equal_to("error")


def test_parse_mypy_invalid_output_returns_empty() -> None:
    """Return empty list when mypy output is not JSON parseable."""
    output = "mypy: command failed"
    issues = parse_mypy_output(output)
    assert_that(issues).is_equal_to([])


def test_parse_mypy_empty_and_whitespace_output() -> None:
    """Return empty list when output is empty or whitespace."""
    assert_that(parse_mypy_output("")).is_empty()
    assert_that(parse_mypy_output("   \n\t")).is_empty()


def test_parse_mypy_json_lines_multiple_issues() -> None:
    """Handle JSON lines payload with multiple issues."""
    output = "\n".join(
        [
            (
                '{"path": "pkg/a.py", "line": 1, "column": 2, '
                '"message": "err A", "code": "A1"}'
            ),
            (
                '{"path": "pkg/b.py", "line": 3, "column": 4, '
                '"message": "err B", "code": "B2"}'
            ),
        ],
    )
    issues = parse_mypy_output(output)

    assert_that(issues).is_length(2)
    assert_that(issues[0].file).ends_with("pkg/a.py")
    assert_that(issues[1].file).ends_with("pkg/b.py")


def test_parse_mypy_multiple_array_entries() -> None:
    """Parse multiple issues from a JSON array."""
    output = (
        "["
        '{"file":"one.py","line":10,"column":1,"message":"first","code":"A"},'
        '{"file":"two.py","line":20,"column":2,"message":"second","code":"B"}'
        "]"
    )
    issues = parse_mypy_output(output)

    assert_that(issues).is_length(2)
    assert_that(issues[0].code).is_equal_to("A")
    assert_that(issues[1].code).is_equal_to("B")


def test_parse_mypy_nested_code_object_variants() -> None:
    """Support nested code objects with alternate keys."""
    output = (
        "{"
        '"errors": ['
        '{"path": "nested.py", "line": 1, "column": 1, '
        '"message": "msg", "code": {"text": "X123"}},'
        '{"path": "nested2.py", "line": 2, "column": 2, '
        '"message": "msg2", "code": {"id": "Y234"}}'
        "]"
        "}"
    )
    issues = parse_mypy_output(output)

    codes = {issue.code for issue in issues}
    assert_that(codes).is_equal_to({"X123", "Y234"})


def test_parse_mypy_field_name_variations() -> None:
    """Handle path/filename/file keys uniformly."""
    output = "\n".join(
        [
            '{"path":"path_variant.py","line":1,"column":1,"message":"one","code":"P"}',
            '{"filename":"filename_variant.py","line":2,"column":2,"message":"two","code":"F"}',
            '{"file":"file_variant.py","line":3,"column":3,"message":"three","code":"L"}',
        ],
    )
    issues = parse_mypy_output(output)

    assert_that(issues).is_length(3)
    assert_that(
        any(issue.file.endswith("path_variant.py") for issue in issues),
    ).is_true()
    assert_that(
        any(issue.file.endswith("filename_variant.py") for issue in issues),
    ).is_true()
    assert_that(
        any(issue.file.endswith("file_variant.py") for issue in issues),
    ).is_true()


def test_parse_mypy_skips_entries_without_file() -> None:
    """Skip entries that lack a file path."""
    output = (
        "{"
        '"errors": ['
        '{"message":"missing file","line":1,"column":1,"code":"X"},'
        '{"path":"valid.py","line":2,"column":2,"message":"ok","code":"OK"}'
        "]"
        "}"
    )
    issues = parse_mypy_output(output)

    assert_that(issues).is_length(1)
    assert_that(issues[0].file).ends_with("valid.py")
