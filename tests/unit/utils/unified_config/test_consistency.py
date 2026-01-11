"""Tests for validate_config_consistency function."""

from __future__ import annotations

from unittest.mock import patch

from assertpy import assert_that

from lintro.utils.unified_config import validate_config_consistency


def test_validate_config_consistency_returns_empty_when_no_effective_line_length() -> (
    None
):
    """Verify empty list when no effective line length is configured."""
    with patch(
        "lintro.utils.config_validation.get_effective_line_length",
        return_value=None,
    ):
        result = validate_config_consistency()
        assert_that(result).is_empty()


def test_validate_config_consistency_detects_mismatch() -> None:
    """Verify warnings are generated for mismatched native configs."""
    with (
        patch(
            "lintro.utils.config_validation.get_effective_line_length",
            return_value=100,
        ),
        patch(
            "lintro.utils.config_validation._load_native_tool_config",
            return_value={"line-length": 88},
        ),
    ):
        result = validate_config_consistency()
        # Should contain at least one warning about the mismatch
        assert_that(result).is_instance_of(list)
        assert_that(result).is_not_empty()


def test_validate_config_consistency_returns_list() -> None:
    """Verify the function always returns a list."""
    with (
        patch(
            "lintro.utils.config_validation.get_effective_line_length",
            return_value=88,
        ),
        patch(
            "lintro.utils.config_validation._load_native_tool_config",
            return_value={},
        ),
    ):
        result = validate_config_consistency()
        assert_that(result).is_instance_of(list)
