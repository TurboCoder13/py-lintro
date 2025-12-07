"""Unit tests for mypy parser."""

from lintro.parsers.mypy.mypy_parser import parse_mypy_output


def test_parse_mypy_json_array() -> None:
    """Parse standard mypy JSON array output."""
    output = (
        '[{"path":"app.py","line":3,"column":5,"endLine":3,"endColumn":10,'
        '"message":"Incompatible return value type","code":"return-value"}]'
    )
    issues = parse_mypy_output(output)

    assert len(issues) == 1
    issue = issues[0]
    assert issue.file.endswith("app.py")
    assert issue.line == 3
    assert issue.column == 5
    assert issue.end_line == 3
    assert issue.end_column == 10
    assert issue.code == "return-value"


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
    assert len(issues) == 1
    issue = issues[0]
    assert issue.file.endswith("service.py")
    assert issue.code == "name-defined"
    assert issue.severity == "error"


def test_parse_mypy_invalid_output_returns_empty() -> None:
    """Return empty list when mypy output is not JSON parseable."""
    output = "mypy: command failed"
    issues = parse_mypy_output(output)
    assert issues == []
