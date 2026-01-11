"""Tests for _load_native_tool_config with pyproject.toml tools."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.utils.native_parsers import _load_native_tool_config


def test_load_native_tool_config_unknown_tool() -> None:
    """Return empty dict for unrecognized tool names."""
    result = _load_native_tool_config("unknown_tool")
    assert_that(result).is_empty()


@pytest.mark.parametrize(
    ("tool_name", "tool_config"),
    [
        ("ruff", {"line-length": 100, "select": ["E", "F"]}),
        ("black", {"line-length": 88}),
        ("bandit", {"exclude_dirs": ["tests"]}),
    ],
    ids=["ruff_config", "black_config", "bandit_config"],
)
def test_load_native_tool_config_from_pyproject(
    tool_name: str,
    tool_config: dict[str, Any],
) -> None:
    """Load tool config from pyproject.toml tool section.

    Args:
        tool_name: Name of the tool to load config for.
        tool_config: Expected configuration dictionary.
    """
    with patch("lintro.utils.config.load_pyproject") as mock_load:
        mock_load.return_value = {"tool": {tool_name: tool_config}}
        result = _load_native_tool_config(tool_name)
        assert_that(result).is_equal_to(tool_config)


@pytest.mark.parametrize(
    ("pyproject_content", "description"),
    [
        ({"tool": "not a dict"}, "tool_section_not_dict"),
        ({"tool": {"ruff": "invalid"}}, "tool_config_not_dict"),
    ],
    ids=["tool_section_not_dict", "specific_tool_config_not_dict"],
)
def test_load_native_tool_config_invalid_pyproject_structure(
    pyproject_content: dict[str, Any],
    description: str,
) -> None:
    """Return empty dict when pyproject.toml has invalid structure.

    Args:
        pyproject_content: Invalid pyproject.toml content structure.
        description: Description of the invalid structure.
    """
    with patch("lintro.utils.config.load_pyproject") as mock_load:
        mock_load.return_value = pyproject_content
        result = _load_native_tool_config("ruff")
        assert_that(result).is_empty()
