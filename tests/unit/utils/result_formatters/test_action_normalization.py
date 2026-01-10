"""Tests for action parameter normalization in print_tool_result."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from assertpy import assert_that

from lintro.enums.action import Action
from lintro.utils.result_formatters import print_tool_result

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.mark.parametrize(
    ("action_value", "expected_behavior"),
    [
        ("check", "success message for no issues"),
        (Action.CHECK, "success message for no issues"),
    ],
    ids=["string_check", "enum_check"],
)
def test_action_normalization_check(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
    action_value: str | Action,
    expected_behavior: str,
) -> None:
    """Verify action parameter accepts both string and enum values.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
        action_value: Action value to test.
        expected_behavior: Expected behavior description.
    """
    mock_console, _ = console_capture_with_kwargs
    mock_success, success_calls = success_capture

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="ruff",
        output="",
        issues_count=0,
        action=action_value,
    )

    assert_that(success_calls).described_as(
        f"Expected {expected_behavior}",
    ).contains("✓ No issues found.")


def test_action_fmt_treated_as_fix(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify 'fmt' string action is treated as fix action.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    output = "Fixed 2 issue(s)\nFound 0 issue(s) that cannot be auto-fixed"

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="ruff",
        output=output,
        issues_count=0,
        action="fmt",
    )

    green_texts = [t for t, kwargs in console_output if kwargs.get("color") == "green"]
    assert_that(any("2 fixed" in t for t in green_texts)).is_true()
