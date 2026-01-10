"""Tests for AsyncToolExecutor.run_tools_parallel method."""

from __future__ import annotations

import asyncio
from typing import Any, cast

from assertpy import assert_that

from lintro.enums.action import Action
from lintro.models.core.tool_result import ToolResult
from lintro.plugins.base import BaseToolPlugin
from lintro.utils.async_tool_executor import AsyncToolExecutor

from .conftest import MockToolDefinition, MockToolPlugin


def test_run_tools_parallel_success(executor: AsyncToolExecutor) -> None:
    """Test parallel execution of multiple tools.

    Args:
        executor: AsyncToolExecutor fixture.
    """
    # MockToolPlugin implements the same interface as BaseToolPlugin for testing
    tools = cast(
        list[tuple[str, BaseToolPlugin]],
        [
            ("tool1", MockToolPlugin(definition=MockToolDefinition(name="tool1"))),
            ("tool2", MockToolPlugin(definition=MockToolDefinition(name="tool2"))),
            ("tool3", MockToolPlugin(definition=MockToolDefinition(name="tool3"))),
        ],
    )

    async def run_test() -> Any:
        return await executor.run_tools_parallel(
            tools,
            paths=["."],
            action=Action.CHECK,
        )

    results = asyncio.run(run_test())

    assert_that(results).is_length(3)
    for _name, result in results:
        assert_that(result.success).is_true()


def test_run_tools_parallel_with_failures(executor: AsyncToolExecutor) -> None:
    """Test parallel execution handles partial failures.

    Args:
        executor: AsyncToolExecutor fixture.
    """
    # MockToolPlugin implements the same interface as BaseToolPlugin for testing
    tools = cast(
        list[tuple[str, BaseToolPlugin]],
        [
            (
                "success_tool",
                MockToolPlugin(definition=MockToolDefinition(name="success_tool")),
            ),
            (
                "failing_tool",
                MockToolPlugin(
                    definition=MockToolDefinition(name="failing_tool"),
                    check_result=ToolResult(
                        name="failing_tool",
                        success=False,
                        output="Failed",
                        issues_count=3,
                    ),
                ),
            ),
        ],
    )

    async def run_test() -> Any:
        return await executor.run_tools_parallel(
            tools,
            paths=["."],
            action=Action.CHECK,
        )

    results = asyncio.run(run_test())

    assert_that(results).is_length(2)
    result_dict = dict(results)
    assert_that(result_dict["success_tool"].success).is_true()
    assert_that(result_dict["failing_tool"].success).is_false()


def test_run_tools_parallel_empty_list(executor: AsyncToolExecutor) -> None:
    """Test parallel execution with empty tools list.

    Args:
        executor: AsyncToolExecutor fixture.
    """

    async def run_test() -> Any:
        return await executor.run_tools_parallel(
            tools=[],
            paths=["."],
            action=Action.CHECK,
        )

    results = asyncio.run(run_test())

    assert_that(results).is_empty()


def test_run_tools_parallel_single_tool(executor: AsyncToolExecutor) -> None:
    """Test parallel execution with single tool.

    Args:
        executor: AsyncToolExecutor fixture.
    """
    # MockToolPlugin implements the same interface as BaseToolPlugin for testing
    tools = cast(
        list[tuple[str, BaseToolPlugin]],
        [
            ("single", MockToolPlugin(definition=MockToolDefinition(name="single"))),
        ],
    )

    async def run_test() -> Any:
        return await executor.run_tools_parallel(
            tools,
            paths=["."],
            action=Action.CHECK,
        )

    results = asyncio.run(run_test())

    assert_that(results).is_length(1)
    assert_that(results[0][0]).is_equal_to("single")


def test_run_tools_parallel_with_options_per_tool(
    executor: AsyncToolExecutor,
) -> None:
    """Test parallel execution passes correct options to each tool.

    Args:
        executor: AsyncToolExecutor fixture.
    """
    tool1_opts: dict[str, Any] = {}
    tool2_opts: dict[str, Any] = {}

    def check1(
        paths: list[str],
        options: dict[str, Any] | None = None,
    ) -> ToolResult:
        nonlocal tool1_opts
        tool1_opts = options or {}
        return ToolResult(name="tool1", success=True, output="", issues_count=0)

    def check2(
        paths: list[str],
        options: dict[str, Any] | None = None,
    ) -> ToolResult:
        nonlocal tool2_opts
        tool2_opts = options or {}
        return ToolResult(name="tool2", success=True, output="", issues_count=0)

    tool1 = MockToolPlugin(definition=MockToolDefinition(name="tool1"))
    # Use object.__setattr__ to bypass dataclass method assignment restriction
    object.__setattr__(tool1, "check", check1)
    tool2 = MockToolPlugin(definition=MockToolDefinition(name="tool2"))
    object.__setattr__(tool2, "check", check2)

    # MockToolPlugin implements the same interface as BaseToolPlugin for testing
    async def run_test() -> Any:
        return await executor.run_tools_parallel(
            tools=cast(
                list[tuple[str, BaseToolPlugin]],
                [("tool1", tool1), ("tool2", tool2)],
            ),
            paths=["."],
            action=Action.CHECK,
            options_per_tool={
                "tool1": {"option_a": "value_a"},
                "tool2": {"option_b": "value_b"},
            },
        )

    asyncio.run(run_test())

    assert_that(tool1_opts).contains_key("option_a")
    assert_that(tool2_opts).contains_key("option_b")
    assert_that(tool1_opts).does_not_contain_key("option_b")
