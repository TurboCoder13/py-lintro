"""Tests for get_parallel_batches function."""

from __future__ import annotations

from unittest.mock import MagicMock

from assertpy import assert_that

from lintro.utils.async_tool_executor import get_parallel_batches


def test_get_parallel_batches_empty_tools_list() -> None:
    """Test batching with empty tools list."""
    mock_manager = MagicMock()

    batches = get_parallel_batches([], mock_manager)

    assert_that(batches).is_empty()


def test_get_parallel_batches_single_tool() -> None:
    """Test single tool results in single batch."""
    mock_manager = MagicMock()
    mock_tool = MagicMock()
    mock_tool.definition.conflicts_with = []
    mock_manager.get_tool.return_value = mock_tool

    batches = get_parallel_batches(["ruff"], mock_manager)

    assert_that(batches).is_length(1)
    assert_that(batches[0]).is_equal_to(["ruff"])


def test_get_parallel_batches_no_conflicts() -> None:
    """Test tools without conflicts go into single batch."""
    mock_manager = MagicMock()

    def get_tool(name: str) -> MagicMock:
        mock = MagicMock()
        mock.definition.conflicts_with = []
        return mock

    mock_manager.get_tool.side_effect = get_tool

    batches = get_parallel_batches(["ruff", "mypy", "bandit"], mock_manager)

    assert_that(batches).is_length(1)
    assert_that(batches[0]).contains("ruff", "mypy", "bandit")


def test_get_parallel_batches_conflicting_tools() -> None:
    """Test conflicting tools are put in separate batches."""
    mock_manager = MagicMock()

    def get_tool(name: str) -> MagicMock:
        mock = MagicMock()
        if name == "black":
            mock.definition.conflicts_with = ["ruff"]
        elif name == "ruff":
            mock.definition.conflicts_with = ["black"]
        else:
            mock.definition.conflicts_with = []
        return mock

    mock_manager.get_tool.side_effect = get_tool

    batches = get_parallel_batches(["black", "ruff", "mypy"], mock_manager)

    assert_that(len(batches)).is_greater_than_or_equal_to(2)

    black_batch = None
    ruff_batch = None
    for i, batch in enumerate(batches):
        if "black" in batch:
            black_batch = i
        if "ruff" in batch:
            ruff_batch = i

    assert_that(black_batch).is_not_equal_to(ruff_batch)


def test_get_parallel_batches_multiple_conflicts() -> None:
    """Test multiple conflicting tool pairs create appropriate batches."""
    mock_manager = MagicMock()

    def get_tool(name: str) -> MagicMock:
        mock = MagicMock()
        conflicts: dict[str, list[str]] = {
            "tool_a": ["tool_b"],
            "tool_b": ["tool_a"],
            "tool_c": ["tool_d"],
            "tool_d": ["tool_c"],
            "tool_e": [],
        }
        mock.definition.conflicts_with = conflicts.get(name, [])
        return mock

    mock_manager.get_tool.side_effect = get_tool

    batches = get_parallel_batches(
        ["tool_a", "tool_b", "tool_c", "tool_d", "tool_e"],
        mock_manager,
    )

    for batch in batches:
        if "tool_a" in batch:
            assert_that(batch).does_not_contain("tool_b")
        if "tool_c" in batch:
            assert_that(batch).does_not_contain("tool_d")


def test_get_parallel_batches_ordering_preserved() -> None:
    """Test that original tool order is preserved within batches."""
    mock_manager = MagicMock()

    def get_tool(name: str) -> MagicMock:
        mock = MagicMock()
        mock.definition.conflicts_with = []
        return mock

    mock_manager.get_tool.side_effect = get_tool

    tools = ["first", "second", "third"]
    batches = get_parallel_batches(tools, mock_manager)

    assert_that(batches[0]).is_equal_to(tools)


def test_get_parallel_batches_handles_missing_tool() -> None:
    """Test graceful handling when tool is not found."""
    mock_manager = MagicMock()

    def get_tool(name: str) -> MagicMock:
        if name == "missing":
            raise KeyError("Tool not found")
        mock = MagicMock()
        mock.definition.conflicts_with = []
        return mock

    mock_manager.get_tool.side_effect = get_tool

    batches = get_parallel_batches(["valid", "missing"], mock_manager)

    assert_that(batches).is_length(1)
    assert_that(batches[0]).contains("valid", "missing")


def test_get_parallel_batches_handles_tool_without_conflicts_attribute() -> None:
    """Test handling tools without conflicts_with attribute."""
    mock_manager = MagicMock()

    def get_tool(name: str) -> MagicMock:
        mock = MagicMock()
        if name == "no_conflicts_attr":
            del mock.definition.conflicts_with
        else:
            mock.definition.conflicts_with = []
        return mock

    mock_manager.get_tool.side_effect = get_tool

    batches = get_parallel_batches(["normal", "no_conflicts_attr"], mock_manager)

    assert_that(batches).is_length(1)
