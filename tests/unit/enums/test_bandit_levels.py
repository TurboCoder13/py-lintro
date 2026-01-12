"""Tests for lintro.enums.bandit_levels module."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.enums.bandit_levels import (
    BanditConfidenceLevel,
    BanditSeverityLevel,
    normalize_bandit_confidence_level,
    normalize_bandit_severity_level,
)


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (BanditSeverityLevel.LOW, "LOW"),
        (BanditSeverityLevel.MEDIUM, "MEDIUM"),
        (BanditSeverityLevel.HIGH, "HIGH"),
    ],
)
def test_severity_level_values(member: BanditSeverityLevel, expected: str) -> None:
    """BanditSeverityLevel members have correct uppercase string values.

    Args:
        member: The BanditSeverityLevel enum member to test.
        expected: The expected string value.
    """
    assert_that(member.value).is_equal_to(expected)


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (BanditConfidenceLevel.LOW, "LOW"),
        (BanditConfidenceLevel.MEDIUM, "MEDIUM"),
        (BanditConfidenceLevel.HIGH, "HIGH"),
    ],
)
def test_confidence_level_values(member: BanditConfidenceLevel, expected: str) -> None:
    """BanditConfidenceLevel members have correct uppercase string values.

    Args:
        member: The BanditConfidenceLevel enum member to test.
        expected: The expected string value.
    """
    assert_that(member.value).is_equal_to(expected)


def test_normalize_severity_from_string() -> None:
    """normalize_bandit_severity_level converts string to BanditSeverityLevel."""
    assert_that(normalize_bandit_severity_level("high")).is_equal_to(
        BanditSeverityLevel.HIGH,
    )


def test_normalize_severity_case_insensitive() -> None:
    """normalize_bandit_severity_level is case-insensitive."""
    assert_that(normalize_bandit_severity_level("HIGH")).is_equal_to(
        BanditSeverityLevel.HIGH,
    )
    assert_that(normalize_bandit_severity_level("High")).is_equal_to(
        BanditSeverityLevel.HIGH,
    )


def test_normalize_severity_passthrough() -> None:
    """normalize_bandit_severity_level returns BanditSeverityLevel unchanged."""
    assert_that(normalize_bandit_severity_level(BanditSeverityLevel.HIGH)).is_equal_to(
        BanditSeverityLevel.HIGH,
    )


def test_normalize_severity_invalid_raises() -> None:
    """normalize_bandit_severity_level raises ValueError for unknown level."""
    with pytest.raises(ValueError, match="Unknown bandit severity level"):
        normalize_bandit_severity_level("critical")


def test_normalize_confidence_from_string() -> None:
    """normalize_bandit_confidence_level converts string to BanditConfidenceLevel."""
    assert_that(normalize_bandit_confidence_level("high")).is_equal_to(
        BanditConfidenceLevel.HIGH,
    )


def test_normalize_confidence_case_insensitive() -> None:
    """normalize_bandit_confidence_level is case-insensitive."""
    assert_that(normalize_bandit_confidence_level("HIGH")).is_equal_to(
        BanditConfidenceLevel.HIGH,
    )
    assert_that(normalize_bandit_confidence_level("High")).is_equal_to(
        BanditConfidenceLevel.HIGH,
    )


def test_normalize_confidence_passthrough() -> None:
    """normalize_bandit_confidence_level returns BanditConfidenceLevel unchanged."""
    assert_that(
        normalize_bandit_confidence_level(BanditConfidenceLevel.HIGH),
    ).is_equal_to(BanditConfidenceLevel.HIGH)


def test_normalize_confidence_invalid_raises() -> None:
    """normalize_bandit_confidence_level raises ValueError for unknown level."""
    with pytest.raises(ValueError, match="Unknown bandit confidence level"):
        normalize_bandit_confidence_level("critical")
