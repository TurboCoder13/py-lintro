"""Tests for field extraction functions."""

from __future__ import annotations

from assertpy import assert_that

from lintro.parsers.base_parser import (
    extract_dict_field,
    extract_int_field,
    extract_str_field,
)

# === Extract Int Field Tests ===


def test_extract_int_field_first_candidate_found() -> None:
    """Return value from first matching candidate key."""
    data: dict[str, object] = {"row": 10, "line": 20}
    result = extract_int_field(data, ["row", "line"])
    assert_that(result).is_equal_to(10)


def test_extract_int_field_second_candidate_found() -> None:
    """Return value from second candidate when first is missing."""
    data: dict[str, object] = {"line": 15}
    result = extract_int_field(data, ["row", "line"])
    assert_that(result).is_equal_to(15)


def test_extract_int_field_no_candidates_found() -> None:
    """Return None when no candidate keys have integer values."""
    data: dict[str, object] = {"other": "value"}
    result = extract_int_field(data, ["row", "line"])
    assert_that(result).is_none()


def test_extract_int_field_with_default() -> None:
    """Return default when no candidate keys have integer values."""
    data: dict[str, object] = {"other": "value"}
    result = extract_int_field(data, ["row", "line"], default=0)
    assert_that(result).is_equal_to(0)


def test_extract_int_field_ignores_non_int_values() -> None:
    """Skip candidate keys with non-integer values."""
    data: dict[str, object] = {"row": "not_an_int", "line": 5}
    result = extract_int_field(data, ["row", "line"])
    assert_that(result).is_equal_to(5)


def test_extract_int_field_empty_candidates() -> None:
    """Return default for empty candidates list."""
    data: dict[str, object] = {"row": 10}
    result = extract_int_field(data, [], default=99)
    assert_that(result).is_equal_to(99)


# === Extract Str Field Tests ===


def test_extract_str_field_first_candidate_found() -> None:
    """Return value from first matching candidate key."""
    data: dict[str, object] = {"filename": "test.py", "file": "other.py"}
    result = extract_str_field(data, ["filename", "file"])
    assert_that(result).is_equal_to("test.py")


def test_extract_str_field_second_candidate_found() -> None:
    """Return value from second candidate when first is missing."""
    data: dict[str, object] = {"file": "test.py"}
    result = extract_str_field(data, ["filename", "file"])
    assert_that(result).is_equal_to("test.py")


def test_extract_str_field_no_candidates_found() -> None:
    """Return empty string when no candidate keys have string values."""
    data: dict[str, object] = {"other": 123}
    result = extract_str_field(data, ["filename", "file"])
    assert_that(result).is_equal_to("")


def test_extract_str_field_with_default() -> None:
    """Return custom default when no candidate keys found."""
    data: dict[str, object] = {"other": 123}
    result = extract_str_field(data, ["filename", "file"], default="unknown")
    assert_that(result).is_equal_to("unknown")


def test_extract_str_field_ignores_non_str_values() -> None:
    """Skip candidate keys with non-string values."""
    data: dict[str, object] = {"filename": 123, "file": "valid.py"}
    result = extract_str_field(data, ["filename", "file"])
    assert_that(result).is_equal_to("valid.py")


# === Extract Dict Field Tests ===


def test_extract_dict_field_first_candidate_found() -> None:
    """Return dict value from first matching candidate key."""
    data: dict[str, object] = {"location": {"line": 1}, "start": {"row": 2}}
    result = extract_dict_field(data, ["location", "start"])
    assert_that(result).is_equal_to({"line": 1})


def test_extract_dict_field_second_candidate_found() -> None:
    """Return dict value from second candidate when first is missing."""
    data: dict[str, object] = {"start": {"row": 2}}
    result = extract_dict_field(data, ["location", "start"])
    assert_that(result).is_equal_to({"row": 2})


def test_extract_dict_field_no_candidates_found() -> None:
    """Return empty dict when no candidate keys have dict values."""
    data: dict[str, object] = {"other": "value"}
    result = extract_dict_field(data, ["location", "start"])
    assert_that(result).is_equal_to({})


def test_extract_dict_field_with_default() -> None:
    """Return custom default when no candidate keys found."""
    default: dict[str, object] = {"default": True}
    data: dict[str, object] = {"other": "value"}
    result = extract_dict_field(data, ["location", "start"], default=default)
    assert_that(result).is_equal_to(default)


def test_extract_dict_field_ignores_non_dict_values() -> None:
    """Skip candidate keys with non-dict values."""
    data: dict[str, object] = {"location": "not_a_dict", "start": {"row": 5}}
    result = extract_dict_field(data, ["location", "start"])
    assert_that(result).is_equal_to({"row": 5})
