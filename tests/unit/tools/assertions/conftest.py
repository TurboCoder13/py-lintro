"""Assertion helper fixtures for tool definition testing.

These fixtures provide reusable assertion helpers for testing
tool plugin definitions across multiple tools.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from assertpy import assert_that


@pytest.fixture
def assert_definition_has_name() -> Callable[[Any, str], None]:
    """Helper to assert a definition has the expected name.

    Returns:
        A callable that asserts definition.name equals expected value.

    Example:
        def test_definition_name(plugin, assert_definition_has_name):
            assert_definition_has_name(plugin.definition, "ruff")
    """

    def _assert(definition: Any, expected_name: str) -> None:
        assert_that(definition.name).is_equal_to(expected_name)

    return _assert


@pytest.fixture
def assert_definition_has_description() -> Callable[[Any], None]:
    """Helper to assert a definition has a non-empty description.

    Returns:
        A callable that asserts definition.description is not empty.

    Example:
        def test_definition_description(plugin, assert_definition_has_description):
            assert_definition_has_description(plugin.definition)
    """

    def _assert(definition: Any) -> None:
        assert_that(definition.description).is_not_empty()

    return _assert


@pytest.fixture
def assert_definition_file_patterns() -> Callable[[Any, list[str]], None]:
    """Helper to assert a definition has expected file patterns.

    Returns:
        A callable that asserts definition.file_patterns contains expected patterns.

    Example:
        def test_definition_patterns(plugin, assert_definition_file_patterns):
            assert_definition_file_patterns(plugin.definition, ["*.py"])
    """

    def _assert(definition: Any, expected_patterns: list[str]) -> None:
        for pattern in expected_patterns:
            assert_that(definition.file_patterns).contains(pattern)

    return _assert


@pytest.fixture
def assert_definition_can_fix() -> Callable[[Any, bool], None]:
    """Helper to assert a definition's can_fix value.

    Returns:
        A callable that asserts definition.can_fix equals expected value.

    Example:
        def test_definition_can_fix(plugin, assert_definition_can_fix):
            assert_definition_can_fix(plugin.definition, True)
    """

    def _assert(definition: Any, expected_can_fix: bool) -> None:
        assert_that(definition.can_fix).is_equal_to(expected_can_fix)

    return _assert


@pytest.fixture
def assert_definition_timeout() -> Callable[[Any, int], None]:
    """Helper to assert a definition's default timeout.

    Returns:
        A callable that asserts definition.default_timeout equals expected value.

    Example:
        def test_definition_timeout(plugin, assert_definition_timeout):
            assert_definition_timeout(plugin.definition, 30)
    """

    def _assert(definition: Any, expected_timeout: int) -> None:
        assert_that(definition.default_timeout).is_equal_to(expected_timeout)

    return _assert
