"""Unit tests for SeverityLevel enum and normalize_severity_level."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.enums.severity_level import (
    SeverityLevel,
    normalize_severity_level,
)

# =============================================================================
# Tests for alias table completeness
# =============================================================================


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param("error", SeverityLevel.ERROR, id="error-lower"),
        pytest.param("ERROR", SeverityLevel.ERROR, id="error-upper"),
        pytest.param("Error", SeverityLevel.ERROR, id="error-mixed"),
        pytest.param("warning", SeverityLevel.WARNING, id="warning-lower"),
        pytest.param("WARNING", SeverityLevel.WARNING, id="warning-upper"),
        pytest.param("info", SeverityLevel.INFO, id="info-lower"),
        pytest.param("INFO", SeverityLevel.INFO, id="info-upper"),
        # Common alternative names → INFO
        pytest.param("note", SeverityLevel.INFO, id="note"),
        pytest.param("hint", SeverityLevel.INFO, id="hint"),
        pytest.param("style", SeverityLevel.INFO, id="style"),
        pytest.param("help", SeverityLevel.INFO, id="help"),
        # Semgrep / Svelte-check
        pytest.param("warn", SeverityLevel.WARNING, id="warn-lower"),
        pytest.param("WARN", SeverityLevel.WARNING, id="warn-upper"),
        # Bandit / cargo-audit levels
        pytest.param("HIGH", SeverityLevel.ERROR, id="high"),
        pytest.param("CRITICAL", SeverityLevel.ERROR, id="critical"),
        pytest.param("MEDIUM", SeverityLevel.WARNING, id="medium"),
        pytest.param("UNKNOWN", SeverityLevel.WARNING, id="unknown"),
        pytest.param("LOW", SeverityLevel.INFO, id="low"),
        # Pytest outcomes
        pytest.param("FAILED", SeverityLevel.ERROR, id="failed"),
        pytest.param("SKIPPED", SeverityLevel.INFO, id="skipped"),
        pytest.param("PASSED", SeverityLevel.INFO, id="passed"),
    ],
)
def test_normalize_maps_alias_to_expected_level(
    raw: str,
    expected: SeverityLevel,
) -> None:
    """normalize_severity_level maps known aliases to the correct level.

    Args:
        raw: The raw severity string to normalize.
        expected: The expected SeverityLevel result.
    """
    assert_that(normalize_severity_level(raw)).is_equal_to(expected)


# =============================================================================
# Case insensitivity
# =============================================================================


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param("Note", id="title-case"),
        pytest.param("nOtE", id="mixed-case"),
        pytest.param("NOTE", id="upper-case"),
        pytest.param("note", id="lower-case"),
    ],
)
def test_normalize_is_case_insensitive(raw: str) -> None:
    """normalize_severity_level is case-insensitive.

    Args:
        raw: The raw severity string with varying case.
    """
    assert_that(normalize_severity_level(raw)).is_equal_to(SeverityLevel.INFO)


# =============================================================================
# Enum passthrough
# =============================================================================


def test_normalize_passes_through_enum_instance() -> None:
    """normalize_severity_level returns enum instances unchanged."""
    for level in SeverityLevel:
        assert_that(normalize_severity_level(level)).is_same_as(level)


# =============================================================================
# Unknown values
# =============================================================================


def test_normalize_raises_for_unknown_value() -> None:
    """normalize_severity_level raises ValueError for unrecognized strings."""
    with pytest.raises(ValueError, match="Unknown severity level"):
        normalize_severity_level("banana")


# =============================================================================
# Alias table sanity
# =============================================================================


def test_alias_table_covers_all_enum_members() -> None:
    """Every SeverityLevel member name can be normalized via the public API."""
    for member in SeverityLevel:
        assert_that(normalize_severity_level(member.name)).is_equal_to(member)
