"""Unit tests for pytest formatter."""

from __future__ import annotations

from assertpy import assert_that

from lintro.formatters.tools.pytest_formatter import (
    PytestFailuresTableDescriptor,
    format_pytest_issues,
)
from lintro.parsers.pytest.pytest_issue import PytestIssue


def test_pytest_table_descriptor_columns() -> None:
    """Test that PytestFailuresTableDescriptor returns correct columns."""
    descriptor = PytestFailuresTableDescriptor()
    columns = descriptor.get_columns()

    expected_columns = ["File", "Status", "Error"]
    assert_that(columns).is_equal_to(expected_columns)


def test_pytest_table_descriptor_rows() -> None:
    """Test that PytestFailuresTableDescriptor generates correct rows."""
    descriptor = PytestFailuresTableDescriptor()

    issues = [
        PytestIssue(
            file="test_example.py",
            line=10,
            test_name="test_failure",
            message="AssertionError: Expected 1 but got 2",
            test_status="FAILED",
            duration=0.001,
            node_id="test_example.py::test_failure",
        ),
        PytestIssue(
            file="test_example.py",
            line=15,
            test_name="test_error",
            message="ZeroDivisionError: division by zero",
            test_status="ERROR",
            duration=0.002,
            node_id="test_example.py::test_error",
        ),
    ]

    rows = descriptor.get_rows(issues)

    assert_that(rows).is_length(2)
    assert_that(rows[0]).is_equal_to(
        [
            "./test_example.py",
            "❌ FAIL",
            "AssertionError: Expected 1 but got 2",
        ],
    )
    assert_that(rows[1]).is_equal_to(
        [
            "./test_example.py",
            "⚠️ ERROR",
            "ZeroDivisionError: division by zero",
        ],
    )


def test_pytest_table_descriptor_rows_no_line() -> None:
    """Test handling issues with no line number."""
    descriptor = PytestFailuresTableDescriptor()

    issues = [
        PytestIssue(
            file="test_example.py",
            line=0,
            test_name="test_failure",
            message="AssertionError",
            test_status="FAILED",
        ),
    ]

    rows = descriptor.get_rows(issues)

    assert_that(rows).is_length(1)
    assert_that(rows[0]).is_equal_to(
        [
            "./test_example.py",
            "❌ FAIL",
            "AssertionError",
        ],
    )


def test_pytest_table_descriptor_rows_long_message() -> None:
    """Test that PytestFailuresTableDescriptor truncates long messages."""
    descriptor = PytestFailuresTableDescriptor()

    long_message = "A" * 150  # 150 characters
    issues = [
        PytestIssue(
            file="test_example.py",
            line=10,
            test_name="test_failure",
            message=long_message,
            test_status="FAILED",
        ),
    ]

    rows = descriptor.get_rows(issues)

    assert_that(rows).is_length(1)
    expected_message = "A" * 100 + "..."
    assert_that(rows[0][2]).is_equal_to(expected_message)


def test_pytest_table_descriptor_rows_empty_test_name() -> None:
    """Test that PytestFailuresTableDescriptor handles empty test names."""
    descriptor = PytestFailuresTableDescriptor()

    issues = [
        PytestIssue(
            file="test_example.py",
            line=10,
            test_name="",
            message="Some error",
            test_status="FAILED",
        ),
    ]

    rows = descriptor.get_rows(issues)

    assert_that(rows).is_length(1)
    assert_that(rows[0]).is_equal_to(
        [
            "./test_example.py",
            "❌ FAIL",
            "Some error",
        ],
    )


def test_format_pytest_issues_empty() -> None:
    """Test formatting empty list of issues."""
    result = format_pytest_issues([])

    # GridStyle returns empty string for empty rows
    assert_that(result).is_equal_to("")


def test_format_pytest_issues_grid_format() -> None:
    """Test formatting issues in grid format."""
    issues = [
        PytestIssue(
            file="test_example.py",
            line=10,
            test_name="test_failure",
            message="AssertionError",
            test_status="FAILED",
        ),
    ]

    result = format_pytest_issues(issues, format="grid")

    assert_that(result).contains("test_example.py")
    assert "❌ FAIL" in result
    assert_that(result).contains("AssertionError")


def test_format_pytest_issues_markdown_format() -> None:
    """Test formatting issues in markdown format."""
    issues = [
        PytestIssue(
            file="test_example.py",
            line=10,
            test_name="test_failure",
            message="AssertionError",
            test_status="FAILED",
        ),
    ]

    result = format_pytest_issues(issues, format="markdown")

    assert_that(result).contains("| File")
    assert_that(result).contains("| ./test_example.py")
    assert_that(result).contains("| ❌ FAIL")
    assert_that(result).contains("| AssertionError")


def test_format_pytest_issues_json_format() -> None:
    """Test formatting issues in JSON format."""
    issues = [
        PytestIssue(
            file="test_example.py",
            line=10,
            test_name="test_failure",
            message="AssertionError",
            test_status="FAILED",
        ),
    ]

    result = format_pytest_issues(issues, format="json")

    # JSON format should contain the tool name (but it's null in this case)
    assert_that(result).contains("tool")
    assert_that(result).contains("test_example.py")
    assert "❌ FAIL" in result
    assert_that(result).contains("AssertionError")


def test_format_pytest_issues_html_format() -> None:
    """Test formatting issues in HTML format."""
    issues = [
        PytestIssue(
            file="test_example.py",
            line=10,
            test_name="test_failure",
            message="AssertionError",
            test_status="FAILED",
        ),
    ]

    result = format_pytest_issues(issues, format="html")

    assert_that(result).contains("<table")
    assert_that(result).contains("test_example.py")
    assert "❌ FAIL" in result
    assert_that(result).contains("AssertionError")


def test_format_pytest_issues_csv_format() -> None:
    """Test formatting issues in CSV format."""
    issues = [
        PytestIssue(
            file="test_example.py",
            line=10,
            test_name="test_failure",
            message="AssertionError",
            test_status="FAILED",
        ),
    ]

    result = format_pytest_issues(issues, format="csv")

    assert_that(result).contains("File,Status,Error")
    assert "test_example.py,❌ FAIL,AssertionError" in result


def test_format_pytest_issues_plain_format() -> None:
    """Test formatting issues in plain format."""
    issues = [
        PytestIssue(
            file="test_example.py",
            line=10,
            test_name="test_failure",
            message="AssertionError",
            test_status="FAILED",
        ),
    ]

    result = format_pytest_issues(issues, format="plain")

    assert_that(result).contains("test_example.py")
    assert "❌ FAIL" in result
    assert_that(result).contains("AssertionError")


def test_format_pytest_issues_default_format() -> None:
    """Test formatting issues with default format."""
    issues = [
        PytestIssue(
            file="test_example.py",
            line=10,
            test_name="test_failure",
            message="AssertionError",
            test_status="FAILED",
        ),
    ]

    result = format_pytest_issues(issues)

    # Default format should be grid
    assert_that(result).contains("test_example.py")
    assert "❌ FAIL" in result
    assert_that(result).contains("AssertionError")


def test_format_pytest_issues_unknown_format() -> None:
    """Test formatting issues with unknown format falls back to grid."""
    issues = [
        PytestIssue(
            file="test_example.py",
            line=10,
            test_name="test_failure",
            message="AssertionError",
            test_status="FAILED",
        ),
    ]

    result = format_pytest_issues(issues, format="unknown")

    # Should fall back to grid format
    assert_that(result).contains("test_example.py")
    assert "❌ FAIL" in result
    assert_that(result).contains("AssertionError")
