"""Tests for pytest output handling in print_tool_result."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from assertpy import assert_that

from lintro.utils.result_formatters import print_tool_result

if TYPE_CHECKING:
    from collections.abc import Callable


def test_pytest_with_output_displays_header(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify pytest output includes test results header and separator.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="pytest",
        output="test_example.py::test_one PASSED",
        issues_count=0,
    )

    texts = [t for t, _ in console_output]
    assert_that(texts).contains("🧪 Test Results")
    assert_that(texts).contains("-" * 20)


def test_pytest_no_issues_no_output_shows_success(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify success message displayed for pytest with no issues and empty output.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, _ = console_capture_with_kwargs
    mock_success, success_calls = success_capture

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="pytest",
        output="",
        issues_count=0,
    )

    assert_that(success_calls).contains("✓ No issues found.")


def test_pytest_filters_json_output_at_line_start(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify standalone JSON lines at start are filtered from pytest output.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    output = '{"key": "value"}\nMore text'

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="pytest",
        output=output,
        issues_count=0,
    )

    texts = [
        t for t, _ in console_output if t and t not in ("🧪 Test Results", "-" * 20, "")
    ]
    combined = "\n".join(texts)
    assert_that(combined).contains("More text")


def test_pytest_preserves_progress_markers(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
) -> None:
    """Verify progress indicators are preserved in pytest output.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    output = "test_file.py [100%]\nAll tests passed"

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name="pytest",
        output=output,
        issues_count=0,
    )

    texts = [
        t for t, _ in console_output if t and t not in ("🧪 Test Results", "-" * 20, "")
    ]
    combined = "\n".join(texts)
    assert_that(combined).contains("[100%]")


@pytest.mark.parametrize(
    ("tool_name", "expected_header"),
    [
        ("pytest", "🧪 Test Results"),
        ("PYTEST", "🧪 Test Results"),
        ("PyTest", "🧪 Test Results"),
    ],
    ids=["lowercase_pytest", "uppercase_pytest", "mixed_case_pytest"],
)
def test_pytest_tool_name_case_insensitive(
    console_capture_with_kwargs: tuple[
        Callable[..., None],
        list[tuple[str, dict[str, Any]]],
    ],
    success_capture: tuple[Callable[[str], None], list[str]],
    tool_name: str,
    expected_header: str,
) -> None:
    """Verify pytest tool name handling is case-insensitive.

    Args:
        console_capture_with_kwargs: Mock console output capture with kwargs.
        success_capture: Mock success message capture.
        tool_name: Name of the tool.
        expected_header: Expected header text.
    """
    mock_console, console_output = console_capture_with_kwargs
    mock_success, _ = success_capture

    print_tool_result(
        console_output_func=mock_console,
        success_func=mock_success,
        tool_name=tool_name,
        output="test output",
        issues_count=0,
    )

    texts = [t for t, _ in console_output]
    assert_that(texts).contains(expected_header)
