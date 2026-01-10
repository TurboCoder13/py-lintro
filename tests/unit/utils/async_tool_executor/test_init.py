"""Tests for AsyncToolExecutor initialization."""

from __future__ import annotations

import os

from assertpy import assert_that

from lintro.utils.async_tool_executor import AsyncToolExecutor


def test_executor_initializes_with_default_workers() -> None:
    """Test executor initializes with default max_workers based on CPU count."""
    exec_instance = AsyncToolExecutor()

    try:
        expected_workers = max(1, min(os.cpu_count() or 4, 32))
        assert_that(exec_instance.max_workers).is_equal_to(expected_workers)
        assert_that(exec_instance._executor).is_not_none()
    finally:
        exec_instance.shutdown()


def test_executor_initializes_with_custom_workers() -> None:
    """Test executor respects custom max_workers value."""
    exec_instance = AsyncToolExecutor(max_workers=8)

    try:
        assert_that(exec_instance.max_workers).is_equal_to(8)
        assert_that(exec_instance._executor).is_not_none()
    finally:
        exec_instance.shutdown()
