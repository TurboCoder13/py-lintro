"""Unit tests for ThreadSafeConsoleLogger metadata and pytest result methods.

Tests cover the _print_metadata_messages helper for parsing tool output
and the _print_pytest_results helper for displaying test results.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.utils.console.logger import ThreadSafeConsoleLogger

# =============================================================================
# Metadata Message Tests
# =============================================================================


@pytest.mark.parametrize(
    ("raw_output", "expected_substring"),
    [
        pytest.param("5 fixable with ruff", "5 auto-fixable", id="fixable-count"),
        pytest.param("0 fixable issues", "No issues found", id="zero-fixable"),
        pytest.param(
            "Some issues cannot be auto-fixed",
            "cannot be auto-fixed",
            id="unfixable",
        ),
        pytest.param(
            "file.py would reformat",
            "would be reformatted",
            id="would-reformat",
        ),
        pytest.param(
            "3 issues fixed successfully",
            "were fixed",
            id="issues-fixed",
        ),
        pytest.param("some random output", "No issues found", id="random-output"),
    ],
)
def test_print_metadata_messages_patterns(
    logger: ThreadSafeConsoleLogger,
    raw_output: str,
    expected_substring: str,
) -> None:
    """Verify _print_metadata_messages handles various output patterns correctly.

    Different tool output patterns should be recognized and formatted into
    user-friendly informational messages.

    Args:
        logger: ThreadSafeConsoleLogger instance fixture.
        raw_output: The raw output to parse for metadata.
        expected_substring: A substring expected in the formatted message.
    """
    with patch.object(logger, "console_output") as mock_output:
        logger._print_metadata_messages(raw_output)
        mock_output.assert_called_once()
        call_text = str(mock_output.call_args)
        assert_that(call_text).contains(expected_substring)


# =============================================================================
# Pytest Results Tests
# =============================================================================


def test_print_pytest_results_success_message(logger: ThreadSafeConsoleLogger) -> None:
    """Verify _print_pytest_results shows success message when tests pass.

    Passing test runs should display a green success indicator with
    'All tests passed' message.

    Args:
        logger: ThreadSafeConsoleLogger instance fixture.
    """
    with patch.object(logger, "console_output") as mock_output:
        logger._print_pytest_results("test output", success=True)
        calls = [str(c) for c in mock_output.call_args_list]
        assert_that(any("All tests passed" in c for c in calls)).is_true()


def test_print_pytest_results_failure_message(logger: ThreadSafeConsoleLogger) -> None:
    """Verify _print_pytest_results shows failure message when tests fail.

    Failing test runs should display a red failure indicator with
    'Some tests failed' message.

    Args:
        logger: ThreadSafeConsoleLogger instance fixture.
    """
    with patch.object(logger, "console_output") as mock_output:
        logger._print_pytest_results("test output", success=False)
        calls = [str(c) for c in mock_output.call_args_list]
        assert_that(any("Some tests failed" in c for c in calls)).is_true()


def test_print_pytest_results_handles_empty_output(
    logger: ThreadSafeConsoleLogger,
) -> None:
    """Verify _print_pytest_results handles empty output gracefully.

    Even with empty output, the header and status message should still
    be displayed to indicate test completion status.

    Args:
        logger: ThreadSafeConsoleLogger instance fixture.
    """
    with patch.object(logger, "console_output") as mock_output:
        logger._print_pytest_results("", success=True)
        # Should still print header and status
        assert_that(mock_output.call_count).is_greater_than(0)


@pytest.mark.parametrize(
    "success",
    [
        pytest.param(True, id="success"),
        pytest.param(False, id="failure"),
    ],
)
def test_print_pytest_results_both_outcomes(
    logger: ThreadSafeConsoleLogger,
    success: bool,
) -> None:
    """Verify _print_pytest_results handles both pass and fail outcomes.

    Both success and failure cases should produce console output with
    appropriate status indicators.

    Args:
        logger: ThreadSafeConsoleLogger instance fixture.
        success: Whether the test run was successful.
    """
    with patch.object(logger, "console_output") as mock_output:
        logger._print_pytest_results("output", success=success)
        assert_that(mock_output.call_count).is_greater_than(0)
