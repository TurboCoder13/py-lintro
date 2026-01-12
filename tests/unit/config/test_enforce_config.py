"""Tests for lintro.config.enforce_config module."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.config.enforce_config import EnforceConfig


def test_enforce_config_default_line_length() -> None:
    """EnforceConfig has None line_length by default."""
    config = EnforceConfig()
    assert_that(config.line_length).is_none()


def test_enforce_config_default_target_python() -> None:
    """EnforceConfig has None target_python by default."""
    config = EnforceConfig()
    assert_that(config.target_python).is_none()


def test_enforce_config_set_line_length() -> None:
    """EnforceConfig accepts line_length value."""
    config = EnforceConfig(line_length=88)
    assert_that(config.line_length).is_equal_to(88)


def test_enforce_config_set_target_python() -> None:
    """EnforceConfig accepts target_python value."""
    config = EnforceConfig(target_python="py313")
    assert_that(config.target_python).is_equal_to("py313")


def test_enforce_config_full_init() -> None:
    """EnforceConfig accepts all parameters."""
    config = EnforceConfig(line_length=120, target_python="py311")
    assert_that(config.line_length).is_equal_to(120)
    assert_that(config.target_python).is_equal_to("py311")


def test_enforce_config_line_length_minimum() -> None:
    """EnforceConfig enforces minimum line_length of 1."""
    with pytest.raises(ValueError, match="greater than or equal to 1"):
        EnforceConfig(line_length=0)


def test_enforce_config_line_length_maximum() -> None:
    """EnforceConfig enforces maximum line_length of 500."""
    with pytest.raises(ValueError, match="less than or equal to 500"):
        EnforceConfig(line_length=501)


def test_enforce_config_line_length_boundary_min() -> None:
    """EnforceConfig accepts minimum line_length of 1."""
    config = EnforceConfig(line_length=1)
    assert_that(config.line_length).is_equal_to(1)


def test_enforce_config_line_length_boundary_max() -> None:
    """EnforceConfig accepts maximum line_length of 500."""
    config = EnforceConfig(line_length=500)
    assert_that(config.line_length).is_equal_to(500)
