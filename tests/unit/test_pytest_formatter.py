"""Unit tests for pytest formatter."""

import pytest

from lintro.formatters.tools.pytest_formatter import (
    PytestTableDescriptor,
    format_pytest_issues,
)
from lintro.parsers.pytest.pytest_issue import PytestIssue


class TestPytestFormatter:
    """Test cases for pytest formatter functions."""

    def test_pytest_table_descriptor_columns(self) -> None:
        """Test that PytestTableDescriptor returns correct columns."""
        descriptor = PytestTableDescriptor()
        columns = descriptor.get_columns()
        
        expected_columns = ["File", "Line", "Test Name", "Status", "Message"]
        assert columns == expected_columns

    def test_pytest_table_descriptor_rows(self) -> None:
        """Test that PytestTableDescriptor generates correct rows."""
        descriptor = PytestTableDescriptor()
        
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
        
        assert len(rows) == 2
        assert rows[0] == [
            "./test_example.py",
            "10",
            "test_failure",
            "FAILED",
            "AssertionError: Expected 1 but got 2",
        ]
        assert rows[1] == [
            "./test_example.py",
            "15",
            "test_error",
            "ERROR",
            "ZeroDivisionError: division by zero",
        ]

    def test_pytest_table_descriptor_rows_no_line(self) -> None:
        """Test that PytestTableDescriptor handles issues with no line number."""
        descriptor = PytestTableDescriptor()
        
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
        
        assert len(rows) == 1
        assert rows[0] == [
            "./test_example.py",
            "-",
            "test_failure",
            "FAILED",
            "AssertionError",
        ]

    def test_pytest_table_descriptor_rows_long_message(self) -> None:
        """Test that PytestTableDescriptor truncates long messages."""
        descriptor = PytestTableDescriptor()
        
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
        
        assert len(rows) == 1
        expected_message = "A" * 100 + "..."
        assert rows[0][4] == expected_message

    def test_pytest_table_descriptor_rows_empty_test_name(self) -> None:
        """Test that PytestTableDescriptor handles empty test names."""
        descriptor = PytestTableDescriptor()
        
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
        
        assert len(rows) == 1
        assert rows[0] == [
            "./test_example.py",
            "10",
            "-",
            "FAILED",
            "Some error",
        ]

    def test_format_pytest_issues_empty(self) -> None:
        """Test formatting empty list of issues."""
        result = format_pytest_issues([])
        
        # GridStyle returns empty string for empty rows
        assert result == ""

    def test_format_pytest_issues_grid_format(self) -> None:
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
        
        assert "test_example.py" in result
        assert "10" in result
        assert "test_failure" in result
        assert "FAILED" in result
        assert "AssertionError" in result

    def test_format_pytest_issues_markdown_format(self) -> None:
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
        
        assert "| File" in result
        assert "| ./test_example.py" in result
        assert "| 10" in result
        assert "| test_failure" in result
        assert "| FAILED" in result
        assert "| AssertionError" in result

    def test_format_pytest_issues_json_format(self) -> None:
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
        assert "tool" in result
        assert "test_example.py" in result
        assert "10" in result
        assert "test_failure" in result
        assert "FAILED" in result
        assert "AssertionError" in result

    def test_format_pytest_issues_html_format(self) -> None:
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
        
        assert "<table" in result
        assert "test_example.py" in result
        assert "10" in result
        assert "test_failure" in result
        assert "FAILED" in result
        assert "AssertionError" in result

    def test_format_pytest_issues_csv_format(self) -> None:
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
        
        assert "File,Line,Test Name,Status,Message" in result
        assert "test_example.py,10,test_failure,FAILED,AssertionError" in result

    def test_format_pytest_issues_plain_format(self) -> None:
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
        
        assert "test_example.py" in result
        assert "10" in result
        assert "test_failure" in result
        assert "FAILED" in result
        assert "AssertionError" in result

    def test_format_pytest_issues_default_format(self) -> None:
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
        assert "test_example.py" in result
        assert "10" in result
        assert "test_failure" in result
        assert "FAILED" in result
        assert "AssertionError" in result

    def test_format_pytest_issues_unknown_format(self) -> None:
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
        assert "test_example.py" in result
        assert "10" in result
        assert "test_failure" in result
        assert "FAILED" in result
        assert "AssertionError" in result
