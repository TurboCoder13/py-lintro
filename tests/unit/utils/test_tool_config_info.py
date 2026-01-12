"""Tests for lintro.utils.tool_config_info module."""

from __future__ import annotations

from assertpy import assert_that


def test_get_tool_config_summary_is_importable() -> None:
    """get_tool_config_summary is importable from tool_config_info."""
    from lintro.utils.tool_config_info import get_tool_config_summary

    assert_that(get_tool_config_summary).is_not_none()
    assert_that(callable(get_tool_config_summary)).is_true()


def test_module_exports_get_tool_config_summary() -> None:
    """Module __all__ exports get_tool_config_summary."""
    from lintro.utils import tool_config_info

    assert_that(tool_config_info.__all__).contains("get_tool_config_summary")
