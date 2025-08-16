from __future__ import annotations

import pytest

from lintro.tools.core.tool_manager import ToolManager
from lintro.tools.tool_enum import ToolEnum


def test_tool_manager_register_and_get_tools():
    tm = ToolManager()
    # Register all known tools from enum
    for enum_member in ToolEnum:
        tm.register_tool(enum_member.value)

    available = tm.get_available_tools()
    assert set(available.keys()) == set(ToolEnum)

    # get_tool returns an instance
    ruff_tool = tm.get_tool(ToolEnum.RUFF)
    assert ruff_tool.name.lower() == "ruff"

    check_tools = tm.get_check_tools()
    fix_tools = tm.get_fix_tools()
    # All tools can check
    assert set(check_tools.keys()) == set(ToolEnum)
    # Some but not all tools can fix
    assert set(fix_tools.keys()) <= set(ToolEnum)


def test_tool_manager_execution_order_and_conflicts(monkeypatch):
    tm = ToolManager()
    for enum_member in ToolEnum:
        tm.register_tool(enum_member.value)

    # Force a conflict between two tools by monkeypatching config
    t1 = tm.get_tool(ToolEnum.RUFF)
    t2 = tm.get_tool(ToolEnum.PRETTIER)
    # Make them conflict with each other
    t1.config.conflicts_with = [ToolEnum.PRETTIER]
    t2.config.conflicts_with = [ToolEnum.RUFF]
    monkeypatch.setattr(
        tm,
        "get_tool",
        lambda e: (
            t1
            if e == ToolEnum.RUFF
            else (t2 if e == ToolEnum.PRETTIER else tm.get_available_tools()[e])
        ),
    )

    order = tm.get_tool_execution_order([ToolEnum.RUFF, ToolEnum.PRETTIER])
    assert len(order) == 1  # one is removed due to conflict

    # With ignore_conflicts, both should appear sorted
    order2 = tm.get_tool_execution_order(
        [ToolEnum.PRETTIER, ToolEnum.RUFF], ignore_conflicts=True
    )
    assert order2 == sorted([ToolEnum.PRETTIER, ToolEnum.RUFF], key=lambda e: e.name)


def test_tool_manager_get_tool_missing():
    tm = ToolManager()
    with pytest.raises(ValueError):
        tm.get_tool(ToolEnum.RUFF)
