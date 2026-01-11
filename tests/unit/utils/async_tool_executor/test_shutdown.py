"""Tests for shutdown functionality."""

from __future__ import annotations

from assertpy import assert_that

from lintro.utils.async_tool_executor import AsyncToolExecutor


def test_shutdown_closes_thread_pool() -> None:
    """Test that shutdown properly closes the thread pool."""
    exec_instance = AsyncToolExecutor(max_workers=2)

    assert_that(exec_instance._executor).is_not_none()

    exec_instance.shutdown()

    assert_that(exec_instance._executor).is_none()


def test_shutdown_can_be_called_multiple_times() -> None:
    """Test that shutdown is idempotent."""
    exec_instance = AsyncToolExecutor(max_workers=2)

    exec_instance.shutdown()
    exec_instance.shutdown()  # Should not raise

    assert_that(exec_instance._executor).is_none()
