"""Tests for output display behavior in print_tool_result."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from assertpy import assert_that

from lintro.utils.result_formatters import print_tool_result

if TYPE_CHECKING:
    from collections.abc import Callable


def test_non_empty_output_is_displayed(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify non-empty output is included in console output.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="ruff",
        output="Some lint output",
        issues_count=1,
    )

    texts = [t for t, _ in console_output]
    assert_that(texts).contains("Some lint output")


def test_whitespace_only_output_not_displayed(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify whitespace-only output results in success message instead.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, _ = console_capture_with_kwargs
    mock_success, success_calls = success_capture

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="ruff",
        output="   \n  \t  ",
        issues_count=0,
    )

    assert_that(success_calls).contains("✓ No issues found.")


def test_blank_line_appended_after_output(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify blank line appended after tool output for visual separation.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="ruff",
        output="",
        issues_count=0,
    )

    assert_that(console_output).is_not_empty()
    last_text, _ = console_output[-1]
    assert_that(last_text).is_equal_to("")
