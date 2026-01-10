"""Tests for _load_native_tool_config with biome."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from assertpy import assert_that

from lintro.utils.native_parsers import _load_native_tool_config


def test_load_biome_config_from_json(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load biome config from biome.json file.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config_file = temp_cwd / "biome.json"
    config_file.write_text('{"formatter": {"indentStyle": "tab"}}')
    result = _load_native_tool_config("biome")
    assert_that(result).is_equal_to({"formatter": {"indentStyle": "tab"}})


def test_load_biome_config_from_jsonc(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load biome config from biome.jsonc with comments stripped.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config_file = temp_cwd / "biome.jsonc"
    config_file.write_text(
        """{
  // Biome configuration
  "formatter": {
    "indentStyle": "space"  // Use spaces
  }
}""",
    )
    result = _load_native_tool_config("biome")
    assert_that(result).is_equal_to({"formatter": {"indentStyle": "space"}})


@pytest.mark.parametrize(
    ("content", "description"),
    [
        ("invalid json {", "invalid_json"),
        ('["invalid"]', "not_a_dict"),
    ],
    ids=["invalid_json_syntax", "json_array_not_dict"],
)
def test_load_biome_config_edge_cases(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
    content: str,
    description: str,
) -> None:
    """Return empty dict for invalid biome.json content.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
        content: Content to write to biome.json.
        description: Description of the test case.
    """
    config_file = temp_cwd / "biome.json"
    config_file.write_text(content)
    result = _load_native_tool_config("biome")
    assert_that(result).is_empty()
