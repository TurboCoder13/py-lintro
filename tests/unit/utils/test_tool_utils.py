"""Tests for lintro.utils.tool_utils module."""

from __future__ import annotations

from assertpy import assert_that

from lintro.utils.tool_utils import VENV_PATTERNS

# =============================================================================
# VENV_PATTERNS tests
# =============================================================================


def test_venv_patterns_is_list() -> None:
    """VENV_PATTERNS is a list."""
    assert_that(VENV_PATTERNS).is_instance_of(list)


def test_venv_patterns_not_empty() -> None:
    """VENV_PATTERNS is not empty."""
    assert_that(VENV_PATTERNS).is_not_empty()


def test_venv_patterns_contains_common_venv_names() -> None:
    """VENV_PATTERNS contains common virtual environment names."""
    assert_that(VENV_PATTERNS).contains("venv")
    assert_that(VENV_PATTERNS).contains(".venv")
    assert_that(VENV_PATTERNS).contains("env")


def test_venv_patterns_contains_node_modules() -> None:
    """VENV_PATTERNS contains node_modules."""
    assert_that(VENV_PATTERNS).contains("node_modules")


def test_venv_patterns_contains_site_packages() -> None:
    """VENV_PATTERNS contains site-packages."""
    assert_that(VENV_PATTERNS).contains("site-packages")


def test_venv_patterns_all_strings() -> None:
    """VENV_PATTERNS contains only strings."""
    for pattern in VENV_PATTERNS:
        assert_that(pattern).is_instance_of(str)
