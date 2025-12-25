"""Unit tests for ToolManager registration and resolution behavior."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.tools.core.tool_manager import ToolManager
from lintro.tools.tool_enum import ToolEnum


def test_tool_manager_register_and_get_tools() -> None:
    """Register all tools and validate discovery and accessors."""
    tm = ToolManager()
    for enum_member in ToolEnum:
        tm.register_tool(enum_member.value)
    available = tm.get_available_tools()
    assert_that(set(available.keys())).is_equal_to(set(ToolEnum))
    ruff_tool = tm.get_tool(ToolEnum.RUFF)
    assert_that(ruff_tool.name.lower()).is_equal_to("ruff")
    check_tools = tm.get_check_tools()
    fix_tools = tm.get_fix_tools()
    assert_that(set(check_tools.keys())).is_equal_to(set(ToolEnum))
    assert_that(set(fix_tools.keys()) <= set(ToolEnum)).is_true()


def test_tool_manager_execution_order_and_conflicts(monkeypatch) -> None:
    """Honor conflicts in execution order unless ignore_conflicts is set.

    Args:
        monkeypatch: Pytest fixture to adjust tool resolver behavior.
    """
    tm = ToolManager()
    for enum_member in ToolEnum:
        tm.register_tool(enum_member.value)
    t1 = tm.get_tool(ToolEnum.RUFF)
    t2 = tm.get_tool(ToolEnum.PRETTIER)
    t1.config.conflicts_with = [ToolEnum.PRETTIER]
    t2.config.conflicts_with = [ToolEnum.RUFF]
    monkeypatch.setattr(
        tm,
        "get_tool",
        lambda e: (
            t1
            if e == ToolEnum.RUFF
            else t2 if e == ToolEnum.PRETTIER else tm.get_available_tools()[e]
        ),
    )
    order = tm.get_tool_execution_order([ToolEnum.RUFF, ToolEnum.PRETTIER])
    assert_that(len(order)).is_equal_to(1)
    order2 = tm.get_tool_execution_order(
        [ToolEnum.PRETTIER, ToolEnum.RUFF],
        ignore_conflicts=True,
    )
    assert_that(order2).is_equal_to(
        sorted([ToolEnum.PRETTIER, ToolEnum.RUFF], key=lambda e: e.name),
    )


def test_tool_manager_get_tool_missing() -> None:
    """Raise ValueError when attempting to get an unregistered tool."""
    tm = ToolManager()
    with pytest.raises(ValueError):
        tm.get_tool(ToolEnum.RUFF)


def test_tool_manager_conflicts_with_strings(monkeypatch) -> None:
    """Verify that conflicts_with with string values are properly detected.

    This test verifies the fix for the bug where string-to-enum comparisons
    in conflicts_with were failing, preventing conflict detection.

    Args:
        monkeypatch: Pytest fixture to adjust tool resolver behavior.
    """
    tm = ToolManager()
    for enum_member in ToolEnum:
        tm.register_tool(enum_member.value)
    t1 = tm.get_tool(ToolEnum.RUFF)
    t2 = tm.get_tool(ToolEnum.PRETTIER)
    # Set conflicts_with using strings (as per type annotation)
    t1.config.conflicts_with = ["prettier"]  # lowercase string
    t2.config.conflicts_with = ["ruff"]  # lowercase string
    monkeypatch.setattr(
        tm,
        "get_tool",
        lambda e: (
            t1
            if e == ToolEnum.RUFF
            else t2 if e == ToolEnum.PRETTIER else tm.get_available_tools()[e]
        ),
    )
    # With conflicts, only one tool should be returned
    order = tm.get_tool_execution_order([ToolEnum.RUFF, ToolEnum.PRETTIER])
    assert_that(len(order)).is_equal_to(1)
    # Verify that conflicts are detected regardless of order
    order2 = tm.get_tool_execution_order([ToolEnum.PRETTIER, ToolEnum.RUFF])
    assert_that(len(order2)).is_equal_to(1)
