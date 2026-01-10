"""Tests for on_result callback functionality."""

from __future__ import annotations

import asyncio
from typing import Any, cast

from assertpy import assert_that

from lintro.enums.action import Action
from lintro.models.core.tool_result import ToolResult
from lintro.plugins.base import BaseToolPlugin
from lintro.utils.async_tool_executor import AsyncToolExecutor

from .conftest import MockToolDefinition, MockToolPlugin


def test_on_result_callback_invoked(executor: AsyncToolExecutor) -> None:
    """Test that on_result callback is invoked for each tool.

    Args:
        executor: AsyncToolExecutor fixture.
    """
    callback_results: list[tuple[str, ToolResult]] = []

    def on_result(name: str, result: ToolResult) -> None:
        callback_results.append((name, result))

    # MockToolPlugin implements the same interface as BaseToolPlugin for testing
    tools = cast(
        list[tuple[str, BaseToolPlugin]],
        [
            ("tool1", MockToolPlugin(definition=MockToolDefinition(name="tool1"))),
            ("tool2", MockToolPlugin(definition=MockToolDefinition(name="tool2"))),
        ],
    )

    async def run_test() -> Any:
        return await executor.run_tools_parallel(
            tools,
            paths=["."],
            action=Action.CHECK,
            on_result=on_result,
        )

    asyncio.run(run_test())

    assert_that(callback_results).is_length(2)
    callback_names = [name for name, _ in callback_results]
    assert_that(callback_names).contains("tool1", "tool2")


def test_on_result_receives_correct_args(executor: AsyncToolExecutor) -> None:
    """Test on_result callback receives correct arguments.

    Args:
        executor: AsyncToolExecutor fixture.
    """
    received_args: list[tuple[str, bool]] = []

    def on_result(name: str, result: ToolResult) -> None:
        received_args.append((name, result.success))

    fail_result = ToolResult(
        name="fail_tool",
        success=False,
        output="",
        issues_count=1,
    )
    # MockToolPlugin implements the same interface as BaseToolPlugin for testing
    tools = cast(
        list[tuple[str, BaseToolPlugin]],
        [
            (
                "success_tool",
                MockToolPlugin(definition=MockToolDefinition(name="success_tool")),
            ),
            (
                "fail_tool",
                MockToolPlugin(
                    definition=MockToolDefinition(name="fail_tool"),
                    check_result=fail_result,
                ),
            ),
        ],
    )

    async def run_test() -> Any:
        return await executor.run_tools_parallel(
            tools,
            paths=["."],
            action=Action.CHECK,
            on_result=on_result,
        )

    asyncio.run(run_test())

    result_dict = dict(received_args)
    assert_that(result_dict["success_tool"]).is_true()
    assert_that(result_dict["fail_tool"]).is_false()
