"""Tests for ruff formatting issue detection in print_tool_result."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from assertpy import assert_that

from lintro.utils.result_formatters import print_tool_result

if TYPE_CHECKING:
    from collections.abc import Callable


def test_ruff_detects_would_reformat_files(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify ruff 'Would reformat' lines are counted as formatting issues.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    output = "Would reformat: file1.py\nWould reformat: file2.py\n[*] 2 fixable"

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="ruff",
        output=output,
        issues_count=4,
        action="check",
    )

    yellow_texts = [
        t for t, kwargs in console_output if kwargs.get("color") == "yellow"
    ]
    combined = " ".join(yellow_texts)
    assert_that(combined).contains("formatting/linting issue(s)")


def test_ruff_detects_files_would_be_reformatted_summary(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify ruff 'N files would be reformatted' summary is detected.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    output = "Formatting issues:\n3 files would be reformatted"

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="ruff",
        output=output,
        issues_count=3,
        action="check",
    )

    yellow_texts = [
        t for t, kwargs in console_output if kwargs.get("color") == "yellow"
    ]
    combined = " ".join(yellow_texts)
    assert_that(combined).contains("formatting/linting issue(s)")


def test_ruff_tool_name_case_insensitive_for_formatting_detection(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify ruff formatting detection works regardless of tool name case.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    output = "Would reformat: file.py\nFormatting issues:"

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="Ruff",
        output=output,
        issues_count=1,
        action="check",
    )

    yellow_texts = [
        t for t, kwargs in console_output if kwargs.get("color") == "yellow"
    ]
    combined = " ".join(yellow_texts)
    assert_that(combined).contains("formatting/linting issue(s)")
