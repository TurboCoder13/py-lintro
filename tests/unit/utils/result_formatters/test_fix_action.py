"""Tests for format/fix action handling in print_tool_result."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from assertpy import assert_that

from lintro.enums.action import Action
from lintro.utils.result_formatters import print_tool_result

if TYPE_CHECKING:
    from collections.abc import Callable


def test_format_action_shows_fixed_and_remaining_counts(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify both fixed and remaining counts displayed for format action.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    output = "Fixed 3 issue(s)\nFound 2 issue(s) that cannot be auto-fixed"

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="black",
        output=output,
        issues_count=0,
        action=Action.FIX,
    )

    texts = [t for t, _ in console_output]
    assert_that(any("3 fixed" in t for t in texts)).is_true()
    assert_that(any("2 remaining" in t for t in texts)).is_true()


def test_format_action_shows_only_fixed_when_no_remaining(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify only fixed count shown when all issues were resolved.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    output = "Fixed 5 issue(s)\nFound 0 issue(s) that cannot be auto-fixed"

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="black",
        output=output,
        issues_count=0,
        action=Action.FIX,
    )

    green_texts = [t for t, kwargs in console_output if kwargs.get("color") == "green"]
    assert_that(any("5 fixed" in t for t in green_texts)).is_true()


def test_format_action_shows_remaining_count_in_red(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify remaining issues count shown in red for format action.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    output = "Fixed 2 issue(s)\nFound 3 issue(s) that cannot be auto-fixed"

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="black",
        output=output,
        issues_count=3,
    )

    red_texts = [t for t, kwargs in console_output if kwargs.get("color") == "red"]
    assert_that(any("3 remaining" in t for t in red_texts)).is_true()


def test_format_action_shows_only_remaining_when_nothing_fixed(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify only remaining count shown when no issues were fixed.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    output = "Found 4 issue(s) that cannot be auto-fixed"

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="black",
        output=output,
        issues_count=4,
    )

    red_texts = [t for t, kwargs in console_output if kwargs.get("color") == "red"]
    assert_that(any("4 remaining" in t for t in red_texts)).is_true()


def test_fix_action_shows_cannot_autofix_message(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify 'cannot be auto-fixed' message shown for fix action with issues.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="black",
        output="Some output",
        issues_count=3,
        action=Action.FIX,
    )

    red_texts = [t for t, kwargs in console_output if kwargs.get("color") == "red"]
    assert_that(any("cannot be auto-fixed" in t for t in red_texts)).is_true()
