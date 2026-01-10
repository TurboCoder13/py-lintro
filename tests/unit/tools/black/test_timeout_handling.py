"""Tests for BlackPlugin timeout handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.black import BlackPlugin


def test_handle_timeout_error_basic(black_plugin: BlackPlugin) -> None:
    """Creates timeout result with basic timeout message.

    Args:
        black_plugin: The BlackPlugin instance to test.
    """
    result = black_plugin._handle_timeout_error(timeout_val=30)

    assert_that(result.success).is_false()
    assert_that(result.output).contains("timed out")
    assert_that(result.output).contains("30s")
    assert_that(result.issues_count).is_equal_to(1)


def test_handle_timeout_error_with_initial_count(black_plugin: BlackPlugin) -> None:
    """Creates timeout result preserving initial count.

    Args:
        black_plugin: The BlackPlugin instance to test.
    """
    result = black_plugin._handle_timeout_error(timeout_val=30, initial_count=5)

    assert_that(result.success).is_false()
    assert_that(result.initial_issues_count).is_equal_to(5)
    assert_that(result.remaining_issues_count).is_equal_to(5)
