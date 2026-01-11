"""Tests for field validation functions."""

from __future__ import annotations

from unittest.mock import patch

from assertpy import assert_that

from lintro.parsers.base_parser import validate_int_field, validate_str_field

# === Validate Str Field Tests ===


def test_validate_str_field_valid_string() -> None:
    """Return string value unchanged."""
    result = validate_str_field("test", "field_name")
    assert_that(result).is_equal_to("test")


def test_validate_str_field_non_string_returns_default() -> None:
    """Return default for non-string values."""
    result = validate_str_field(123, "field_name", default="unknown")
    assert_that(result).is_equal_to("unknown")


def test_validate_str_field_none_returns_default() -> None:
    """Return default for None values."""
    result = validate_str_field(None, "field_name", default="default")
    assert_that(result).is_equal_to("default")


def test_validate_str_field_logs_warning() -> None:
    """Log warning when log_warning is True and type mismatches."""
    with patch("lintro.parsers.base_parser.logger") as mock_logger:
        validate_str_field(123, "test_field", log_warning=True)
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert_that(call_args).contains("test_field")
        assert_that(call_args).contains("int")


def test_validate_str_field_no_warning_for_none() -> None:
    """Do not log warning for None values."""
    with patch("lintro.parsers.base_parser.logger") as mock_logger:
        validate_str_field(None, "test_field", log_warning=True)
        mock_logger.warning.assert_not_called()


# === Validate Int Field Tests ===


def test_validate_int_field_valid_int() -> None:
    """Return integer value unchanged."""
    result = validate_int_field(42, "field_name")
    assert_that(result).is_equal_to(42)


def test_validate_int_field_non_int_returns_default() -> None:
    """Return default for non-integer values."""
    result = validate_int_field("not_int", "field_name", default=0)
    assert_that(result).is_equal_to(0)


def test_validate_int_field_bool_returns_default() -> None:
    """Return default for boolean values (bools are not treated as ints)."""
    result = validate_int_field(True, "field_name", default=-1)
    assert_that(result).is_equal_to(-1)


def test_validate_int_field_none_returns_default() -> None:
    """Return default for None values."""
    result = validate_int_field(None, "field_name", default=99)
    assert_that(result).is_equal_to(99)


def test_validate_int_field_logs_warning() -> None:
    """Log warning when log_warning is True and type mismatches."""
    with patch("lintro.parsers.base_parser.logger") as mock_logger:
        validate_int_field("bad", "line_number", log_warning=True)
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert_that(call_args).contains("line_number")
