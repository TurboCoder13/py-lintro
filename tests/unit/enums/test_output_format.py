"""Tests for lintro.enums.output_format module."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.enums.output_format import OutputFormat, normalize_output_format


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (OutputFormat.PLAIN, "plain"),
        (OutputFormat.GRID, "grid"),
        (OutputFormat.MARKDOWN, "markdown"),
        (OutputFormat.HTML, "html"),
        (OutputFormat.JSON, "json"),
        (OutputFormat.CSV, "csv"),
    ],
)
def test_output_format_values(member: OutputFormat, expected: str) -> None:
    """OutputFormat members have correct lowercase string values.

    Args:
        member: The OutputFormat enum member to test.
        expected: The expected string value.
    """
    assert_that(member.value).is_equal_to(expected)


def test_output_format_is_str_enum() -> None:
    """OutputFormat members are string instances."""
    assert_that(OutputFormat.GRID).is_instance_of(str)


def test_normalize_output_format_from_string() -> None:
    """normalize_output_format converts string to OutputFormat."""
    assert_that(normalize_output_format("json")).is_equal_to(OutputFormat.JSON)


def test_normalize_output_format_case_insensitive() -> None:
    """normalize_output_format is case-insensitive."""
    assert_that(normalize_output_format("JSON")).is_equal_to(OutputFormat.JSON)
    assert_that(normalize_output_format("Json")).is_equal_to(OutputFormat.JSON)


def test_normalize_output_format_passthrough() -> None:
    """normalize_output_format returns OutputFormat unchanged."""
    assert_that(normalize_output_format(OutputFormat.JSON)).is_equal_to(
        OutputFormat.JSON,
    )


def test_normalize_output_format_invalid_defaults_to_grid() -> None:
    """normalize_output_format defaults to GRID for invalid values."""
    assert_that(normalize_output_format("invalid")).is_equal_to(OutputFormat.GRID)


def test_normalize_output_format_none_defaults_to_grid() -> None:
    """normalize_output_format defaults to GRID for None."""
    # None has no .upper() method, triggers AttributeError
    assert_that(normalize_output_format(None)).is_equal_to(OutputFormat.GRID)  # type: ignore[arg-type]
