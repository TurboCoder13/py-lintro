"""Tests for _load_native_tool_config with markdownlint."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from lintro.utils.native_parsers import _load_native_tool_config


def test_load_markdownlint_config_from_json(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load markdownlint config from .markdownlint.json file.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config_file = temp_cwd / ".markdownlint.json"
    config_file.write_text('{"MD013": false}')
    result = _load_native_tool_config("markdownlint")
    assert_that(result).is_equal_to({"MD013": False})


def test_load_markdownlint_config_from_jsonc(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load markdownlint config from .markdownlint.jsonc with comments.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config_file = temp_cwd / ".markdownlint.jsonc"
    config_file.write_text(
        """{
  // Disable line length
  "MD013": false
}""",
    )
    result = _load_native_tool_config("markdownlint")
    assert_that(result).is_equal_to({"MD013": False})


def test_load_markdownlint_config_from_yaml(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load markdownlint config from .markdownlint.yaml file.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config_file = temp_cwd / ".markdownlint.yaml"
    config_file.write_text("MD013: false\nMD001: true\n")
    result = _load_native_tool_config("markdownlint")
    assert_that(result).is_equal_to({"MD013": False, "MD001": True})


def test_load_markdownlint_config_yaml_not_installed(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Skip YAML config files when yaml module is not available.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config_file = temp_cwd / ".markdownlint.yaml"
    config_file.write_text("MD013: false\n")
    with patch("lintro.utils.native_parsers.yaml", None):
        result = _load_native_tool_config("markdownlint")
        assert_that(result).is_empty()


def test_load_markdownlint_config_yaml_multi_document(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Handle multi-document YAML by using the first document.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config_file = temp_cwd / ".markdownlint.yaml"
    config_file.write_text("MD013: false\n")
    with patch("lintro.utils.native_parsers.yaml") as mock_yaml:
        mock_yaml.safe_load.return_value = [{"MD013": False}, {"MD001": True}]
        result = _load_native_tool_config("markdownlint")
        assert_that(result).is_equal_to({"MD013": False})


@pytest.mark.parametrize(
    ("filename", "content", "description"),
    [
        (".markdownlint.json", "not valid json", "invalid_json"),
        (".markdownlint.json", '["invalid"]', "not_a_dict"),
        (".markdownlint.yaml", "invalid: yaml: [", "invalid_yaml"),
    ],
    ids=["invalid_json_syntax", "json_array_not_dict", "invalid_yaml_syntax"],
)
def test_load_markdownlint_config_edge_cases(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
    filename: str,
    content: str,
    description: str,
) -> None:
    """Return empty dict for various invalid markdownlint config scenarios.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
        filename: Name of the config file to create.
        content: Content to write to the config file.
        description: Description of the test case.
    """
    config_file = temp_cwd / filename
    config_file.write_text(content)
    result = _load_native_tool_config("markdownlint")
    assert_that(result).is_empty()
