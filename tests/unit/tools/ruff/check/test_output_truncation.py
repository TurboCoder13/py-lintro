"""Tests for output truncation in execute_ruff_check."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from assertpy import assert_that

from lintro.tools.implementations.ruff.check import execute_ruff_check


def test_check_failure_truncates_long_output_in_warning(
    mock_ruff_tool: MagicMock,
) -> None:
    """Verify long check output is truncated in warning log.

    When ruff check fails with output > 2000 chars, the warning should show
    truncated output with a note about seeing debug.log for full output.

    Args:
        mock_ruff_tool: Mock RuffTool instance for testing.
    """
    # Create output longer than 2000 chars
    long_output = "x" * 3000

    with (
        patch(
            "lintro.tools.implementations.ruff.check.walk_files_with_excludes",
            return_value=["test.py"],
        ),
        patch(
            "lintro.tools.implementations.ruff.check.run_subprocess_with_timeout",
            return_value=(False, long_output),
        ),
        patch(
            "lintro.tools.implementations.ruff.check.parse_ruff_output",
            return_value=[],
        ),
        patch("lintro.tools.implementations.ruff.check.logger") as mock_logger,
    ):
        execute_ruff_check(mock_ruff_tool, ["/test/project"])

        # Verify warning was called with truncated message
        mock_logger.warning.assert_called()
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        truncation_logged = any("1000 more chars" in call for call in warning_calls)
        assert_that(truncation_logged).described_as(
            f"Expected truncation message in warning calls: {warning_calls}",
        ).is_true()


def test_format_check_failure_truncates_long_output_in_warning(
    mock_ruff_tool: MagicMock,
) -> None:
    """Verify long format check output is truncated in warning log.

    When ruff format --check fails with output > 2000 chars, the warning should
    show truncated output with a note about seeing debug.log for full output.

    Args:
        mock_ruff_tool: Mock RuffTool instance for testing.
    """
    mock_ruff_tool.options["format_check"] = True

    # Create output longer than 2000 chars
    long_format_output = "Would reformat: " + "x" * 3000

    with (
        patch(
            "lintro.tools.implementations.ruff.check.walk_files_with_excludes",
            return_value=["test.py"],
        ),
        patch(
            "lintro.tools.implementations.ruff.check.run_subprocess_with_timeout",
        ) as mock_subprocess,
        patch(
            "lintro.tools.implementations.ruff.check.parse_ruff_output",
            return_value=[],
        ),
        patch(
            "lintro.tools.implementations.ruff.check.parse_ruff_format_check_output",
            return_value=[],
        ),
        patch("lintro.tools.implementations.ruff.check.logger") as mock_logger,
    ):
        # First call succeeds (lint), second call fails (format)
        mock_subprocess.side_effect = [
            (True, "[]"),
            (False, long_format_output),
        ]

        execute_ruff_check(mock_ruff_tool, ["/test/project"])

        # Verify warning was called with truncated message
        mock_logger.warning.assert_called()
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        truncation_logged = any("more chars" in call for call in warning_calls)
        assert_that(truncation_logged).described_as(
            f"Expected truncation message in warning calls: {warning_calls}",
        ).is_true()


def test_check_failure_does_not_truncate_short_output(
    mock_ruff_tool: MagicMock,
) -> None:
    """Verify short check output is not truncated in warning log.

    When ruff check fails with output < 2000 chars, the warning should show
    the full output without any truncation message.

    Args:
        mock_ruff_tool: Mock RuffTool instance for testing.
    """
    short_output = "Error: something went wrong"

    with (
        patch(
            "lintro.tools.implementations.ruff.check.walk_files_with_excludes",
            return_value=["test.py"],
        ),
        patch(
            "lintro.tools.implementations.ruff.check.run_subprocess_with_timeout",
            return_value=(False, short_output),
        ),
        patch(
            "lintro.tools.implementations.ruff.check.parse_ruff_output",
            return_value=[],
        ),
        patch("lintro.tools.implementations.ruff.check.logger") as mock_logger,
    ):
        execute_ruff_check(mock_ruff_tool, ["/test/project"])

        # Verify warning was called without truncation message
        mock_logger.warning.assert_called()
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        truncation_logged = any("more chars" in call for call in warning_calls)
        assert_that(truncation_logged).described_as(
            f"Did not expect truncation message: {warning_calls}",
        ).is_false()
