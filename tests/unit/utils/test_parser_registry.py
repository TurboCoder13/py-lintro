"""Unit tests for parser_registry module."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from assertpy import assert_that

from lintro.utils.output.parser_registration import (
    ParserError,
    _parse_bandit_output,
)
from lintro.utils.output.parser_registry import ParserEntry, ParserRegistry


@pytest.fixture(autouse=True)
def reset_registry() -> Generator[None, None, None]:
    """Reset the parser registry before and after each test.

    Yields:
        None: After clearing the registry and before restoring.
    """
    # Store original parsers
    original_parsers = ParserRegistry._parsers.copy()
    ParserRegistry.clear()
    yield
    # Restore original parsers
    ParserRegistry._parsers = original_parsers


# =============================================================================
# ParserEntry tests
# =============================================================================


def test_parser_entry_creation() -> None:
    """Create a ParserEntry with parse function only."""

    def dummy_parser(output: str) -> list[Any]:
        return []

    entry = ParserEntry(parse_func=dummy_parser)
    assert_that(entry.parse_func).is_same_as(dummy_parser)
    assert_that(entry.is_fixable).is_none()


def test_parser_entry_with_fixability() -> None:
    """Create a ParserEntry with fixability predicate."""

    def dummy_parser(output: str) -> list[Any]:
        return []

    def is_fixable(issue: object) -> bool:
        return True

    entry = ParserEntry(parse_func=dummy_parser, is_fixable=is_fixable)
    assert_that(entry.parse_func).is_same_as(dummy_parser)
    assert_that(entry.is_fixable).is_same_as(is_fixable)


# =============================================================================
# ParserRegistry.register tests
# =============================================================================


def test_register_parser() -> None:
    """Register a parser for a tool."""

    def my_parser(output: str) -> list[Any]:
        return [{"issue": "test"}]

    ParserRegistry.register("mytool", my_parser)
    assert_that(ParserRegistry.is_registered("mytool")).is_true()


def test_register_parser_case_insensitive() -> None:
    """Tool names are stored in lowercase."""

    def my_parser(output: str) -> list[Any]:
        return []

    ParserRegistry.register("MyTool", my_parser)
    assert_that(ParserRegistry.is_registered("mytool")).is_true()
    assert_that(ParserRegistry.is_registered("MYTOOL")).is_true()
    assert_that(ParserRegistry.is_registered("MyTool")).is_true()


def test_register_parser_with_fixability() -> None:
    """Register a parser with fixability predicate."""

    def my_parser(output: str) -> list[Any]:
        return []

    def my_fixable(issue: object) -> bool:
        return hasattr(issue, "fixable")

    ParserRegistry.register("mytool", my_parser, is_fixable=my_fixable)
    entry = ParserRegistry.get("mytool")
    assert_that(entry).is_not_none()
    assert_that(entry.is_fixable).is_same_as(my_fixable)  # type: ignore[union-attr]


# =============================================================================
# ParserRegistry.get tests
# =============================================================================


def test_get_registered_parser() -> None:
    """Get a registered parser entry."""

    def my_parser(output: str) -> list[Any]:
        return []

    ParserRegistry.register("mytool", my_parser)
    entry = ParserRegistry.get("mytool")
    assert_that(entry).is_not_none()
    assert_that(entry.parse_func).is_same_as(my_parser)  # type: ignore[union-attr]


def test_get_unregistered_parser_returns_none() -> None:
    """Get returns None for unregistered tools."""
    entry = ParserRegistry.get("unknown_tool")
    assert_that(entry).is_none()


# =============================================================================
# ParserRegistry.parse tests
# =============================================================================


def test_parse_with_registered_parser() -> None:
    """Parse output using registered parser."""

    def my_parser(output: str) -> list[Any]:
        return [{"line": 1, "message": output}]

    ParserRegistry.register("mytool", my_parser)
    result = ParserRegistry.parse("mytool", "test output")
    assert_that(result).is_length(1)
    assert_that(result[0]["message"]).is_equal_to("test output")


def test_parse_unknown_tool_returns_empty() -> None:
    """Parse returns empty list for unknown tools."""
    result = ParserRegistry.parse("unknown_tool", "some output")
    assert_that(result).is_empty()


def test_parse_case_insensitive() -> None:
    """Parse works with any case of tool name."""

    def my_parser(output: str) -> list[Any]:
        return [{"found": True}]

    ParserRegistry.register("MyTool", my_parser)
    result = ParserRegistry.parse("mytool", "test")
    assert_that(result).is_length(1)


# =============================================================================
# ParserRegistry.get_fixability_predicate tests
# =============================================================================


def test_get_fixability_predicate_registered() -> None:
    """Get fixability predicate for registered tool."""

    def my_parser(output: str) -> list[Any]:
        return []

    def my_fixable(issue: object) -> bool:
        return True

    ParserRegistry.register("mytool", my_parser, is_fixable=my_fixable)
    predicate = ParserRegistry.get_fixability_predicate("mytool")
    assert_that(predicate).is_same_as(my_fixable)


def test_get_fixability_predicate_no_predicate() -> None:
    """Get returns None when tool has no fixability predicate."""

    def my_parser(output: str) -> list[Any]:
        return []

    ParserRegistry.register("mytool", my_parser)
    predicate = ParserRegistry.get_fixability_predicate("mytool")
    assert_that(predicate).is_none()


def test_get_fixability_predicate_unknown_tool() -> None:
    """Get returns None for unknown tools."""
    predicate = ParserRegistry.get_fixability_predicate("unknown_tool")
    assert_that(predicate).is_none()


# =============================================================================
# ParserRegistry.clear tests
# =============================================================================


def test_clear_removes_all_parsers() -> None:
    """Clear removes all registered parsers."""

    def my_parser(output: str) -> list[Any]:
        return []

    ParserRegistry.register("tool1", my_parser)
    ParserRegistry.register("tool2", my_parser)
    assert_that(ParserRegistry.is_registered("tool1")).is_true()
    assert_that(ParserRegistry.is_registered("tool2")).is_true()

    ParserRegistry.clear()
    assert_that(ParserRegistry.is_registered("tool1")).is_false()
    assert_that(ParserRegistry.is_registered("tool2")).is_false()


# =============================================================================
# ParserRegistry.is_registered tests
# =============================================================================


def test_is_registered_true() -> None:
    """Check if a tool is registered."""

    def my_parser(output: str) -> list[Any]:
        return []

    ParserRegistry.register("mytool", my_parser)
    assert_that(ParserRegistry.is_registered("mytool")).is_true()


def test_is_registered_false() -> None:
    """Check returns False for unregistered tools."""
    assert_that(ParserRegistry.is_registered("unknown_tool")).is_false()


# =============================================================================
# ParserError tests
# =============================================================================


def test_parser_error_raised_on_parsing_failure() -> None:
    """Parser raises ParserError when parsing fails instead of returning empty list."""
    with pytest.raises(ParserError) as exc_info:
        _parse_bandit_output("not valid json")

    assert_that(str(exc_info.value)).contains("Failed to parse Bandit output")


def test_parser_error_raised_on_empty_output() -> None:
    """Parser raises ParserError for empty output."""
    with pytest.raises(ParserError) as exc_info:
        _parse_bandit_output("")

    assert_that(str(exc_info.value)).contains("Failed to parse Bandit output")


def test_parser_error_preserves_original_exception() -> None:
    """ParserError preserves the original exception as its cause."""
    with pytest.raises(ParserError) as exc_info:
        _parse_bandit_output("{invalid json")

    assert_that(exc_info.value.__cause__).is_not_none()
