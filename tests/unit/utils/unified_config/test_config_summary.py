"""Tests for get_tool_config_summary function."""

from __future__ import annotations

from unittest.mock import patch

from assertpy import assert_that

from lintro.utils.unified_config import ToolConfigInfo, get_tool_config_summary


def test_get_tool_config_summary_returns_dict_for_all_standard_tools() -> None:
    """Verify config summary includes all standard tools."""
    with (
        patch(
            "lintro.utils.config_validation._load_native_tool_config",
            return_value={},
        ),
        patch(
            "lintro.utils.config_validation.load_lintro_tool_config",
            return_value={},
        ),
        patch(
            "lintro.utils.config_validation.get_effective_line_length",
            return_value=88,
        ),
        patch(
            "lintro.utils.config_validation.validate_config_consistency",
            return_value=[],
        ),
    ):
        result = get_tool_config_summary()

        assert_that(result).contains_key("ruff")
        assert_that(result).contains_key("black")
        assert_that(result).contains_key("prettier")
        assert_that(result).contains_key("yamllint")
        assert_that(result).contains_key("markdownlint")


def test_get_tool_config_summary_returns_tool_config_info_instances() -> None:
    """Verify each tool gets a proper ToolConfigInfo instance."""
    with (
        patch(
            "lintro.utils.config_validation._load_native_tool_config",
            return_value={},
        ),
        patch(
            "lintro.utils.config_validation.load_lintro_tool_config",
            return_value={},
        ),
        patch(
            "lintro.utils.config_validation.get_effective_line_length",
            return_value=88,
        ),
        patch(
            "lintro.utils.config_validation.validate_config_consistency",
            return_value=[],
        ),
    ):
        result = get_tool_config_summary()

        assert_that(result["ruff"]).is_instance_of(ToolConfigInfo)
        assert_that(result["ruff"].tool_name).is_equal_to("ruff")


def test_get_tool_config_summary_includes_effective_line_length() -> None:
    """Verify effective line_length is included in effective_config."""
    with (
        patch(
            "lintro.utils.config_validation._load_native_tool_config",
            return_value={},
        ),
        patch(
            "lintro.utils.config_validation.load_lintro_tool_config",
            return_value={},
        ),
        patch(
            "lintro.utils.config_validation.get_effective_line_length",
            return_value=120,
        ),
        patch(
            "lintro.utils.config_validation.validate_config_consistency",
            return_value=[],
        ),
    ):
        result = get_tool_config_summary()

        assert_that(result["ruff"].effective_config).contains_key("line_length")
        assert_that(result["ruff"].effective_config["line_length"]).is_equal_to(120)
