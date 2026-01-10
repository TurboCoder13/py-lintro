"""Tests for get_effective_line_length function."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from assertpy import assert_that

from lintro.utils.unified_config import get_effective_line_length


def test_get_effective_line_length_from_tool_config() -> None:
    """Verify line_length from tool-specific lintro config has highest priority."""
    with patch(
        "lintro.utils.config_priority.load_lintro_tool_config",
        return_value={"line_length": 100},
    ):
        result = get_effective_line_length("ruff")
        assert_that(result).is_equal_to(100)


def test_get_effective_line_length_from_tool_config_hyphen_key() -> None:
    """Verify line-length (hyphenated) key is also supported in tool config."""
    with patch(
        "lintro.utils.config_priority.load_lintro_tool_config",
        return_value={"line-length": 120},
    ):
        result = get_effective_line_length("ruff")
        assert_that(result).is_equal_to(120)


def test_get_effective_line_length_from_global_config() -> None:
    """Verify global lintro config is used when tool config is empty."""
    with (
        patch("lintro.utils.config_priority.load_lintro_tool_config", return_value={}),
        patch(
            "lintro.utils.config_priority.load_lintro_global_config",
            return_value={"line_length": 80},
        ),
    ):
        result = get_effective_line_length("ruff")
        assert_that(result).is_equal_to(80)


def test_get_effective_line_length_from_global_config_hyphen_key() -> None:
    """Verify line-length (hyphenated) key is also supported in global config."""
    with (
        patch("lintro.utils.config_priority.load_lintro_tool_config", return_value={}),
        patch(
            "lintro.utils.config_priority.load_lintro_global_config",
            return_value={"line-length": 90},
        ),
    ):
        result = get_effective_line_length("ruff")
        assert_that(result).is_equal_to(90)


def test_get_effective_line_length_from_ruff_config() -> None:
    """Verify Ruff config in pyproject.toml is used as fallback."""
    with (
        patch("lintro.utils.config_priority.load_lintro_tool_config", return_value={}),
        patch(
            "lintro.utils.config_priority.load_lintro_global_config",
            return_value={},
        ),
        patch(
            "lintro.utils.config_priority.load_pyproject",
            return_value={"tool": {"ruff": {"line-length": 88}}},
        ),
    ):
        result = get_effective_line_length("black")
        assert_that(result).is_equal_to(88)


def test_get_effective_line_length_from_ruff_config_underscore_key() -> None:
    """Verify line_length (underscore) key is also supported in Ruff config."""
    with (
        patch("lintro.utils.config_priority.load_lintro_tool_config", return_value={}),
        patch(
            "lintro.utils.config_priority.load_lintro_global_config",
            return_value={},
        ),
        patch(
            "lintro.utils.config_priority.load_pyproject",
            return_value={"tool": {"ruff": {"line_length": 95}}},
        ),
    ):
        result = get_effective_line_length("black")
        assert_that(result).is_equal_to(95)


def test_get_effective_line_length_returns_none_when_no_config(
    mock_empty_configs: Any,
) -> None:
    """Verify None is returned when no line length is configured anywhere.

    Args:
        mock_empty_configs: Mock for empty config loaders.
    """
    result = get_effective_line_length("unknown_tool")
    assert_that(result).is_none()
