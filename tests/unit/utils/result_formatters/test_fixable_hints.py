"""Tests for fixable issue hints in print_tool_result."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from assertpy import assert_that

from lintro.enums.action import Action
from lintro.utils.result_formatters import print_tool_result

if TYPE_CHECKING:
    from collections.abc import Callable


def test_fixable_hint_shown_in_check_mode(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify hint about fixable issues shown in check mode.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    output = "[*] 5 fixable with the `--fix` flag"

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="ruff",
        output=output,
        issues_count=5,
        action="check",
    )

    yellow_texts = [
        t for t, kwargs in console_output if kwargs.get("color") == "yellow"
    ]
    assert_that(
        any("5 formatting/linting issue(s)" in t for t in yellow_texts),
    ).is_true()
    assert_that(any("lintro format" in t for t in yellow_texts)).is_true()


def test_fixable_hint_sums_multiple_matches(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify multiple fixable counts are summed from output.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    output = "[*] 3 fixable\n[*] 2 fixable"

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="ruff",
        output=output,
        issues_count=5,
        action="check",
    )

    yellow_texts = [
        t for t, kwargs in console_output if kwargs.get("color") == "yellow"
    ]
    assert_that(
        any("5 formatting/linting issue(s)" in t for t in yellow_texts),
    ).is_true()


def test_fixable_hint_uses_raw_output_for_meta(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify raw_output_for_meta used for fixable detection.

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
        output="Formatted output without fixable info",
        issues_count=3,
        raw_output_for_meta="[*] 3 fixable",
        action="check",
    )

    yellow_texts = [
        t for t, kwargs in console_output if kwargs.get("color") == "yellow"
    ]
    assert_that(
        any("3 formatting/linting issue(s)" in t for t in yellow_texts),
    ).is_true()


def test_no_fixable_hint_in_fix_action(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify fixable hint not shown when already running fix action.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    output = "[*] 5 fixable"

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="ruff",
        output=output,
        issues_count=5,
        action=Action.FIX,
    )

    yellow_texts = [
        t for t, kwargs in console_output if kwargs.get("color") == "yellow"
    ]
    assert_that(any("lintro format" in t for t in yellow_texts)).is_false()
