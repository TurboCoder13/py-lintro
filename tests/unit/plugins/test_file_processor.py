"""Unit tests for file processor module."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.parsers.base_issue import BaseIssue
from lintro.plugins.file_processor import AggregatedResult, FileProcessingResult

# =============================================================================
# Tests for FileProcessingResult dataclass
# =============================================================================


def test_file_processing_result_success() -> None:
    """FileProcessingResult stores success state correctly."""
    result = FileProcessingResult(
        success=True,
        output="No issues found",
        issues=[],
    )
    assert_that(result.success).is_true()
    assert_that(result.output).is_equal_to("No issues found")
    assert_that(result.issues).is_empty()
    assert_that(result.skipped).is_false()
    assert_that(result.error).is_none()


def test_file_processing_result_with_issues() -> None:
    """FileProcessingResult stores issues correctly."""
    issue = BaseIssue(file="test.txt", line=1, message="Test issue")
    result = FileProcessingResult(
        success=False,
        output="Found 1 issue",
        issues=[issue],
    )
    assert_that(result.success).is_false()
    assert_that(result.issues).is_length(1)
    assert_that(result.issues[0].message).is_equal_to("Test issue")


def test_file_processing_result_skipped() -> None:
    """FileProcessingResult marks skipped files correctly."""
    result = FileProcessingResult(
        success=False,
        output="",
        issues=[],
        skipped=True,
    )
    assert_that(result.skipped).is_true()


def test_file_processing_result_with_error() -> None:
    """FileProcessingResult stores error messages correctly."""
    result = FileProcessingResult(
        success=False,
        output="",
        issues=[],
        error="Connection timeout",
    )
    assert_that(result.error).is_equal_to("Connection timeout")


# =============================================================================
# Tests for AggregatedResult dataclass
# =============================================================================


def test_aggregated_result_defaults() -> None:
    """AggregatedResult has correct default values."""
    result = AggregatedResult()
    assert_that(result.all_success).is_true()
    assert_that(result.all_issues).is_empty()
    assert_that(result.all_outputs).is_empty()
    assert_that(result.skipped_files).is_empty()
    assert_that(result.execution_failures).is_equal_to(0)
    assert_that(result.total_issues).is_equal_to(0)


# =============================================================================
# Tests for AggregatedResult.add_file_result method
# =============================================================================


def test_add_file_result_success() -> None:
    """Add successful file result updates aggregated state correctly."""
    aggregated = AggregatedResult()
    file_result = FileProcessingResult(
        success=True,
        output="",
        issues=[],
    )

    aggregated.add_file_result("/path/to/file.txt", file_result)

    assert_that(aggregated.all_success).is_true()
    assert_that(aggregated.total_issues).is_equal_to(0)
    assert_that(aggregated.all_outputs).is_empty()


def test_add_file_result_with_issues() -> None:
    """Add file result with issues updates aggregated state correctly."""
    aggregated = AggregatedResult()
    issue = BaseIssue(file="test.txt", line=1, message="Test issue")
    file_result = FileProcessingResult(
        success=True,
        output="Found 1 issue",
        issues=[issue],
    )

    aggregated.add_file_result("/path/to/test.txt", file_result)

    assert_that(aggregated.all_success).is_true()
    assert_that(aggregated.total_issues).is_equal_to(1)
    assert_that(aggregated.all_issues).is_length(1)
    assert_that(aggregated.all_outputs).is_length(1)


def test_add_file_result_failure() -> None:
    """Add failed file result updates all_success correctly."""
    aggregated = AggregatedResult()
    file_result = FileProcessingResult(
        success=False,
        output="Error occurred",
        issues=[],
    )

    aggregated.add_file_result("/path/to/file.txt", file_result)

    assert_that(aggregated.all_success).is_false()
    assert_that(aggregated.all_outputs).contains("Error occurred")


def test_add_file_result_skipped() -> None:
    """Add skipped file result updates skipped_files correctly."""
    aggregated = AggregatedResult()
    file_result = FileProcessingResult(
        success=False,
        output="",
        issues=[],
        skipped=True,
    )

    aggregated.add_file_result("/path/to/file.txt", file_result)

    assert_that(aggregated.all_success).is_false()
    assert_that(aggregated.skipped_files).contains("/path/to/file.txt")
    assert_that(aggregated.execution_failures).is_equal_to(1)


def test_add_file_result_with_error() -> None:
    """Add file result with error updates execution_failures correctly."""
    aggregated = AggregatedResult()
    file_result = FileProcessingResult(
        success=False,
        output="",
        issues=[],
        error="Connection refused",
    )

    aggregated.add_file_result("/path/to/file.txt", file_result)

    assert_that(aggregated.all_success).is_false()
    assert_that(aggregated.execution_failures).is_equal_to(1)
    assert_that(aggregated.all_outputs[0]).contains("Connection refused")


def test_add_multiple_file_results() -> None:
    """Add multiple file results accumulates correctly."""
    aggregated = AggregatedResult()

    # First file: success with issues
    issue1 = BaseIssue(file="file1.txt", line=1, message="Issue 1")
    result1 = FileProcessingResult(
        success=True,
        output="File 1 output",
        issues=[issue1],
    )
    aggregated.add_file_result("/path/to/file1.txt", result1)

    # Second file: failure
    result2 = FileProcessingResult(
        success=False,
        output="File 2 error",
        issues=[],
    )
    aggregated.add_file_result("/path/to/file2.txt", result2)

    # Third file: success with multiple issues
    issue2 = BaseIssue(file="file3.txt", line=2, message="Issue 2")
    issue3 = BaseIssue(file="file3.txt", line=5, message="Issue 3")
    result3 = FileProcessingResult(
        success=True,
        output="File 3 output",
        issues=[issue2, issue3],
    )
    aggregated.add_file_result("/path/to/file3.txt", result3)

    assert_that(aggregated.all_success).is_false()
    assert_that(aggregated.total_issues).is_equal_to(3)
    assert_that(aggregated.all_issues).is_length(3)
    assert_that(aggregated.all_outputs).is_length(3)


# =============================================================================
# Tests for AggregatedResult.build_output method
# =============================================================================


def test_build_output_empty() -> None:
    """Build output returns None when no output."""
    aggregated = AggregatedResult()
    output = aggregated.build_output()
    assert_that(output).is_none()


def test_build_output_with_outputs() -> None:
    """Build output combines all outputs correctly."""
    aggregated = AggregatedResult()
    aggregated.all_outputs = ["Output 1", "Output 2"]

    output = aggregated.build_output()

    assert_that(output).contains("Output 1")
    assert_that(output).contains("Output 2")
    assert_that(output).contains("\n")


def test_build_output_with_skipped_files() -> None:
    """Build output includes skipped files information."""
    aggregated = AggregatedResult()
    aggregated.skipped_files = ["/path/to/file1.txt", "/path/to/file2.txt"]
    aggregated.execution_failures = 2

    output = aggregated.build_output()

    assert_that(output).is_not_none()
    assert_that(output).contains("Skipped/failed 2 file(s)")
    assert_that(output).contains("/path/to/file1.txt")
    assert_that(output).contains("/path/to/file2.txt")


def test_build_output_with_timeout() -> None:
    """Build output includes timeout value when provided."""
    aggregated = AggregatedResult()
    aggregated.skipped_files = ["/path/to/file.txt"]
    aggregated.execution_failures = 1

    output = aggregated.build_output(timeout=30)

    assert_that(output).is_not_none()
    assert_that(output).contains("timeout: 30s")


def test_build_output_with_execution_errors() -> None:
    """Build output includes execution error count."""
    aggregated = AggregatedResult()
    aggregated.execution_failures = 3

    output = aggregated.build_output()

    assert_that(output).is_not_none()
    assert_that(output).contains("Failed to process 3 file(s)")


def test_build_output_combines_outputs_and_errors() -> None:
    """Build output combines regular outputs and error information."""
    aggregated = AggregatedResult()
    aggregated.all_outputs = ["Regular output"]
    aggregated.skipped_files = ["/path/to/skipped.txt"]
    aggregated.execution_failures = 1

    output = aggregated.build_output(timeout=60)

    assert_that(output).is_not_none()
    assert_that(output).contains("Regular output")
    assert_that(output).contains("Skipped/failed 1 file(s)")
    assert_that(output).contains("timeout: 60s")


# =============================================================================
# Tests for edge cases
# =============================================================================


def test_empty_output_not_added() -> None:
    """Empty output from successful file is not added to all_outputs."""
    aggregated = AggregatedResult()
    file_result = FileProcessingResult(
        success=True,
        output="",
        issues=[],
    )

    aggregated.add_file_result("/path/to/file.txt", file_result)

    assert_that(aggregated.all_outputs).is_empty()


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("   ", None),
        ("\n\n", None),
        ("\t", None),
        ("", None),
    ],
    ids=[
        "whitespace_only",
        "newlines_only",
        "tab_only",
        "empty_string",
    ],
)
def test_build_output_whitespace_returns_none(
    output: str,
    expected: str | None,
) -> None:
    """Build output returns None for whitespace-only outputs.

    Args:
        output: The whitespace-only output string to test.
        expected: The expected result (None for whitespace-only).
    """
    aggregated = AggregatedResult()
    aggregated.all_outputs = [output]

    result = aggregated.build_output()

    assert_that(result).is_equal_to(expected)
