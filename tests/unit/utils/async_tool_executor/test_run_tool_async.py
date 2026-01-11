"""Tests for AsyncToolExecutor.run_tool_async method."""

from __future__ import annotations

import asyncio
from typing import Any, cast

from assertpy import assert_that

from lintro.enums.action import Action
from lintro.models.core.tool_result import ToolResult
from lintro.plugins.base import BaseToolPlugin
from lintro.utils.async_tool_executor import AsyncToolExecutor

from .conftest import MockToolDefinition, MockToolPlugin


def test_run_tool_async_check_success(executor: AsyncToolExecutor) -> None:
    """Test successful async execution of check action.

    Args:
        executor: AsyncToolExecutor fixture.
    """
    tool = MockToolPlugin(
        definition=MockToolDefinition(name="test_tool"),
    )

    async def run_test() -> Any:
        # MockToolPlugin implements the same interface as BaseToolPlugin for testing
        return await executor.run_tool_async(
            cast(BaseToolPlugin, tool),
            paths=["."],
            action=Action.CHECK,
        )

    result = asyncio.run(run_test())

    assert_that(result.success).is_true()
    assert_that(result.name).is_equal_to("test_tool")
    assert_that(tool.check_called).is_true()
    assert_that(tool.fix_called).is_false()


def test_run_tool_async_fix_success(executor: AsyncToolExecutor) -> None:
    """Test successful async execution of fix action.

    Args:
        executor: AsyncToolExecutor fixture.
    """
    tool = MockToolPlugin(
        definition=MockToolDefinition(name="fix_tool"),
    )

    async def run_test() -> Any:
        # MockToolPlugin implements the same interface as BaseToolPlugin for testing
        return await executor.run_tool_async(
            cast(BaseToolPlugin, tool),
            paths=["."],
            action=Action.FIX,
        )

    result = asyncio.run(run_test())

    assert_that(result.success).is_true()
    assert_that(tool.fix_called).is_true()
    assert_that(tool.check_called).is_false()


def test_run_tool_async_with_options(executor: AsyncToolExecutor) -> None:
    """Test async execution passes options correctly.

    Args:
        executor: AsyncToolExecutor fixture.
    """
    received_options: dict[str, Any] = {}

    def check_with_capture(
        paths: list[str],
        options: dict[str, Any] | None = None,
    ) -> ToolResult:
        nonlocal received_options
        received_options = options or {}
        return ToolResult(
            name="capture_tool",
            success=True,
            output="",
            issues_count=0,
        )

    tool = MockToolPlugin(definition=MockToolDefinition(name="capture_tool"))
    # Use object.__setattr__ to bypass dataclass method assignment restriction
    object.__setattr__(tool, "check", check_with_capture)

    async def run_test() -> Any:
        # MockToolPlugin implements the same interface as BaseToolPlugin for testing
        return await executor.run_tool_async(
            cast(BaseToolPlugin, tool),
            paths=["."],
            action=Action.CHECK,
            options={"verbose": True, "fix": False},
        )

    asyncio.run(run_test())

    assert_that(received_options).contains_key("verbose")
    assert_that(received_options["verbose"]).is_true()


def test_run_tool_async_with_failure(executor: AsyncToolExecutor) -> None:
    """Test async execution handles tool failure.

    Args:
        executor: AsyncToolExecutor fixture.
    """
    failed_result = ToolResult(
        name="failing_tool",
        success=False,
        output="Error occurred",
        issues_count=5,
    )
    tool = MockToolPlugin(
        definition=MockToolDefinition(name="failing_tool"),
        check_result=failed_result,
    )

    async def run_test() -> Any:
        # MockToolPlugin implements the same interface as BaseToolPlugin for testing
        return await executor.run_tool_async(
            cast(BaseToolPlugin, tool),
            paths=["."],
            action=Action.CHECK,
        )

    result = asyncio.run(run_test())

    assert_that(result.success).is_false()
    assert_that(result.issues_count).is_equal_to(5)
