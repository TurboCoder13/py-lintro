"""Tests for ToolConfigInfo dataclass."""

from __future__ import annotations

import dataclasses

from assertpy import assert_that

from lintro.utils.unified_config import ToolConfigInfo


def test_tool_config_info_default_values() -> None:
    """Verify ToolConfigInfo has expected default values."""
    info = ToolConfigInfo(tool_name="ruff")

    assert_that(info.tool_name).is_equal_to("ruff")
    assert_that(info.native_config).is_empty()
    assert_that(info.lintro_tool_config).is_empty()
    assert_that(info.effective_config).is_empty()
    assert_that(info.warnings).is_empty()
    assert_that(info.is_injectable).is_true()


def test_tool_config_info_with_all_values() -> None:
    """Verify ToolConfigInfo stores all provided values correctly."""
    info = ToolConfigInfo(
        tool_name="black",
        native_config={"line-length": 88},
        lintro_tool_config={"strict": True},
        effective_config={"line_length": 100},
        warnings=["Warning 1"],
        is_injectable=False,
    )

    assert_that(info.tool_name).is_equal_to("black")
    assert_that(info.native_config).is_equal_to({"line-length": 88})
    assert_that(info.lintro_tool_config).is_equal_to({"strict": True})
    assert_that(info.effective_config).is_equal_to({"line_length": 100})
    assert_that(info.warnings).is_length(1)
    assert_that(info.warnings[0]).is_equal_to("Warning 1")
    assert_that(info.is_injectable).is_false()


def test_tool_config_info_is_dataclass_instance() -> None:
    """Verify ToolConfigInfo instances are proper dataclass instances."""
    info = ToolConfigInfo(tool_name="prettier")
    assert_that(dataclasses.is_dataclass(info)).is_true()
