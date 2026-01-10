"""Unit tests for ThreadSafeConsoleLogger header display methods.

Tests cover the lintro header, tool header, and post-checks header
formatting and display functionality.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.utils.console.logger import ThreadSafeConsoleLogger


def test_print_lintro_header_with_run_dir(tmp_path: Path) -> None:
    """Verify print_lintro_header outputs header when run directory exists.

    When configured with a run_dir, the header should display a message
    indicating where output files will be generated, followed by a blank line.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    logger = ThreadSafeConsoleLogger(run_dir=tmp_path)
    with patch.object(logger, "console_output") as mock_output:
        logger.print_lintro_header()
        # Should be called twice: header message and blank line
        assert_that(mock_output.call_count).is_equal_to(2)
        # Verify first call contains the run directory path
        first_call_text = mock_output.call_args_list[0].kwargs.get(
            "text",
            (
                mock_output.call_args_list[0].args[0]
                if mock_output.call_args_list[0].args
                else ""
            ),
        )
        assert_that(str(tmp_path) in first_call_text).is_true()


def test_print_lintro_header_without_run_dir_is_noop(
    logger: ThreadSafeConsoleLogger,
) -> None:
    """Verify print_lintro_header does nothing without run directory.

    Without a run_dir, there's no output location to announce, so the
    header should be skipped entirely.

    Args:
        logger: ThreadSafeConsoleLogger instance fixture.
    """
    with patch.object(logger, "console_output") as mock_output:
        logger.print_lintro_header()
        mock_output.assert_not_called()


def test_print_tool_header_outputs_formatted_header(
    logger: ThreadSafeConsoleLogger,
) -> None:
    """Verify print_tool_header outputs a formatted banner for tool execution.

    The tool header should include borders, the tool name, action, and
    decorative emoji elements to visually separate tool output sections.

    Args:
        logger: ThreadSafeConsoleLogger instance fixture.
    """
    with patch.object(logger, "console_output") as mock_output:
        logger.print_tool_header("ruff", "check")
        # Should output: border, header text, border, blank line
        assert_that(mock_output.call_count).is_equal_to(4)


@pytest.mark.parametrize(
    ("tool_name", "action"),
    [
        pytest.param("ruff", "check", id="ruff-check"),
        pytest.param("black", "fmt", id="black-fmt"),
        pytest.param("mypy", "check", id="mypy-check"),
        pytest.param("pytest", "test", id="pytest-test"),
    ],
)
def test_print_tool_header_various_tools(
    logger: ThreadSafeConsoleLogger,
    tool_name: str,
    action: str,
) -> None:
    """Verify print_tool_header works with various tool and action combinations.

    Different tools should produce appropriate headers with their names
    and corresponding actions displayed correctly.

    Args:
        logger: ThreadSafeConsoleLogger instance fixture.
        tool_name: The name of the tool to display.
        action: The action being performed.
    """
    with patch.object(logger, "console_output") as mock_output:
        logger.print_tool_header(tool_name, action)
        assert_that(mock_output.call_count).is_equal_to(4)
        # Verify tool name appears in the header
        header_text = str(mock_output.call_args_list[1])
        assert_that(header_text).contains(tool_name)


def test_print_post_checks_header_outputs_styled_header(
    logger: ThreadSafeConsoleLogger,
) -> None:
    """Verify print_post_checks_header outputs a distinctive styled header.

    The post-checks header uses a different style (magenta, heavy borders)
    to visually separate optional follow-up checks from primary tool runs.

    Args:
        logger: ThreadSafeConsoleLogger instance fixture.
    """
    with patch.object(logger, "console_output") as mock_output:
        logger.print_post_checks_header()
        # Should output: border, title, subtitle, border, blank line
        assert_that(mock_output.call_count).is_equal_to(5)
