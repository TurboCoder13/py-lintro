"""Tests for JSON parsing edge cases and potential security issues.

These tests verify that JSON parsing handles malformed, large, and
potentially malicious input safely without causing DoS or crashes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from assertpy import assert_that

from lintro.parsers.base_issue import BaseIssue
from lintro.parsers.streaming import (
    collect_streaming_results,
    stream_json_array_fallback,
    stream_json_lines,
)


@dataclass
class SimpleIssue(BaseIssue):
    """Simple issue class for testing."""

    code: str = "TEST001"
    severity: str = "error"


def simple_parse_item(item: dict[str, object]) -> SimpleIssue | None:
    """Parse a simple item for testing.

    Args:
        item: Dictionary to parse.

    Returns:
        SimpleIssue or None.
    """
    file = item.get("file", "")
    message = item.get("message", "")
    if isinstance(file, str) and isinstance(message, str):
        return SimpleIssue(file=file, line=1, column=1, message=message)
    return None


# =============================================================================
# Tests for stream_json_lines edge cases
# =============================================================================


def test_json_lines_empty_input() -> None:
    """Verify empty input returns no results."""
    results = list(stream_json_lines("", simple_parse_item))
    assert_that(results).is_empty()


def test_json_lines_whitespace_only_input() -> None:
    """Verify whitespace-only input returns no results."""
    results = list(stream_json_lines("   \n\n   \n", simple_parse_item))
    assert_that(results).is_empty()


def test_json_lines_invalid_json_lines_skipped() -> None:
    """Verify invalid JSON lines are skipped without crashing."""
    input_data = '{"file": "a.py"}\nnot json\n{"file": "b.py"}\n'
    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_length(2)


def test_json_lines_truncated_json_skipped() -> None:
    """Verify truncated JSON is skipped."""
    input_data = '{"file": "a.py"}\n{"file": "incomplete\n{"file": "b.py"}\n'
    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_length(2)


def test_json_lines_non_dict_json_skipped() -> None:
    """Verify non-dict JSON values are skipped."""
    input_data = '{"file": "a.py"}\n["array"]\n"string"\n123\nnull\n'
    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_length(1)


def test_json_lines_special_characters() -> None:
    """Verify JSON with special characters is handled."""
    input_data = '{"file": "path/with spaces.py", "message": "quote: \\"test\\""}\n'
    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_length(1)
    assert_that(results[0].file).is_equal_to("path/with spaces.py")


def test_json_lines_unicode() -> None:
    """Verify JSON with unicode characters is handled."""
    input_data = '{"file": "file_\u00e9\u00e8.py", "message": "\u4e2d\u6587"}\n'
    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_length(1)


def test_json_lines_emoji() -> None:
    """Verify JSON with emoji is handled."""
    input_data = '{"file": "test.py", "message": "Error: \U0001f4a5 boom"}\n'
    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_length(1)


def test_json_lines_deeply_nested() -> None:
    """Verify deeply nested JSON doesn't cause stack overflow."""
    nested: dict[str, object] = {"file": "test.py", "meta": {}}
    current = nested["meta"]
    for _ in range(50):  # 50 levels deep
        current["level"] = {}  # type: ignore[index]
        current = current["level"]  # type: ignore[index]

    input_data = json.dumps(nested) + "\n"
    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_length(1)


def test_json_lines_large_json_object() -> None:
    """Verify large JSON object is handled without memory issues."""
    large_value = "x" * (1024 * 1024)  # 1MB
    input_data = f'{{"file": "test.py", "message": "{large_value}"}}\n'

    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_length(1)
    assert_that(len(results[0].message)).is_equal_to(1024 * 1024)


def test_json_lines_many_lines() -> None:
    """Verify many JSON lines are processed efficiently."""
    lines = [f'{{"file": "file{i}.py", "message": "msg"}}' for i in range(1000)]
    input_data = "\n".join(lines)

    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_length(1000)


def test_json_lines_mixed_valid_invalid() -> None:
    """Verify mixed valid/invalid lines don't stop processing."""
    input_data = "\n".join(
        [
            '{"file": "1.py"}',
            "invalid",
            '{"file": "2.py"}',
            "{incomplete",
            '{"file": "3.py"}',
            "",
            '{"file": "4.py"}',
        ],
    )

    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_length(4)


def test_json_lines_parser_exception_handling() -> None:
    """Verify parser exceptions don't crash the stream."""

    def failing_parser(item: dict[str, object]) -> SimpleIssue | None:
        if item.get("fail"):
            raise ValueError("Intentional failure")
        return simple_parse_item(item)

    input_data = '{"file": "1.py"}\n{"fail": true}\n{"file": "2.py"}\n'
    results = list(stream_json_lines(input_data, failing_parser))
    assert_that(results).is_length(2)


def test_json_lines_not_starting_with_brace_skipped() -> None:
    """Verify non-JSON-object lines are skipped."""
    input_data = "Info: starting\n{'file': 'test.py'}\n[1,2,3]\n"
    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_empty()


# =============================================================================
# Tests for stream_json_array_fallback edge cases
# =============================================================================


def test_json_array_empty_array() -> None:
    """Verify empty array returns no results."""
    results = list(stream_json_array_fallback("[]", simple_parse_item))
    assert_that(results).is_empty()


def test_json_array_empty_object() -> None:
    """Verify empty object returns no results."""
    results = list(stream_json_array_fallback("{}", simple_parse_item))
    assert_that(results).is_empty()


def test_json_array_empty_string() -> None:
    """Verify empty string returns no results."""
    results = list(stream_json_array_fallback("", simple_parse_item))
    assert_that(results).is_empty()


def test_json_array_valid_array() -> None:
    """Verify valid array is parsed correctly."""
    input_data = '[{"file": "a.py"}, {"file": "b.py"}]'
    results = list(stream_json_array_fallback(input_data, simple_parse_item))
    assert_that(results).is_length(2)


def test_json_array_with_trailing_data() -> None:
    """Verify array with trailing non-JSON data is handled."""
    input_data = '[{"file": "a.py"}]\nSome trailing text'
    results = list(stream_json_array_fallback(input_data, simple_parse_item))
    assert_that(results).is_length(1)


def test_json_array_fallback_to_json_lines() -> None:
    """Verify fallback to JSON Lines when array fails."""
    input_data = '{"file": "a.py"}\n{"file": "b.py"}\n'
    results = list(stream_json_array_fallback(input_data, simple_parse_item))
    assert_that(results).is_length(2)


def test_json_array_non_dict_items_skipped() -> None:
    """Verify non-dict items in array are skipped."""
    input_data = '[{"file": "a.py"}, "string", 123, null]'
    results = list(stream_json_array_fallback(input_data, simple_parse_item))
    assert_that(results).is_length(1)


def test_json_array_large_array() -> None:
    """Verify large array is processed."""
    items = [f'{{"file": "file{i}.py"}}' for i in range(500)]
    input_data = "[" + ",".join(items) + "]"

    results = list(stream_json_array_fallback(input_data, simple_parse_item))
    assert_that(results).is_length(500)


# =============================================================================
# Tests for collect_streaming_results helper
# =============================================================================


def test_collect_streaming_results_collects_all() -> None:
    """Verify all results are collected into list."""
    input_data = '{"file": "a.py"}\n{"file": "b.py"}\n{"file": "c.py"}\n'
    gen = stream_json_lines(input_data, simple_parse_item)

    results = collect_streaming_results(gen)
    assert_that(results).is_length(3)
    assert_that(results).is_instance_of(list)


def test_collect_streaming_results_empty_generator() -> None:
    """Verify empty generator returns empty list."""
    gen = stream_json_lines("", simple_parse_item)
    results = collect_streaming_results(gen)
    assert_that(results).is_empty()


# =============================================================================
# Tests for JSON security concerns
# =============================================================================


def test_json_bomb_protection() -> None:
    """Verify JSON bomb (exponential expansion) doesn't crash.

    Note: Python's json module handles this reasonably well,
    but we test to ensure we don't introduce our own issues.
    This test verifies that moderately nested JSON doesn't cause issues.
    """
    data = {"a": {"b": {"c": {"d": {"e": {"f": "value"}}}}}}
    input_data = json.dumps(data) + "\n"

    # Should process without crashing (may or may not match our simple parser)
    results = list(stream_json_lines(input_data, simple_parse_item))
    # Just verify processing completed - results depend on parse function
    # (parser returns issue with empty file/message for nested data)
    assert_that(results).is_not_none()


def test_json_null_bytes() -> None:
    """Verify null bytes in JSON strings are handled."""
    input_data = '{"file": "test\\u0000.py", "message": "null byte"}\n'
    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_length(1)
    assert_that(results[0].file).contains("\x00")


def test_json_control_characters() -> None:
    """Verify control characters in JSON are handled."""
    input_data = '{"file": "test.py", "message": "tab:\\there"}\n'
    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_length(1)
    assert_that(results[0].message).contains("\t")


def test_json_very_long_string_keys() -> None:
    """Verify very long string keys don't cause issues."""
    long_key = "k" * 10000
    input_data = f'{{"{long_key}": "value", "file": "test.py"}}\n'
    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_length(1)


def test_json_many_keys_in_object() -> None:
    """Verify objects with many keys are handled."""
    keys = [f'"key{i}": "value"' for i in range(1000)]
    input_data = '{"file": "test.py", ' + ", ".join(keys) + "}\n"
    results = list(stream_json_lines(input_data, simple_parse_item))
    assert_that(results).is_length(1)
