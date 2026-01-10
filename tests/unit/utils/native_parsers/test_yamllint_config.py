"""Tests for _load_native_tool_config with yamllint."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from lintro.utils.native_parsers import _load_native_tool_config


def test_load_yamllint_config_from_file(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load yamllint config from .yamllint file in current directory.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config_file = temp_cwd / ".yamllint"
    config_file.write_text("rules:\n  line-length: 120\n")
    result = _load_native_tool_config("yamllint")
    assert_that(result).is_equal_to({"rules": {"line-length": 120}})


def test_load_yamllint_config_yaml_not_installed(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Return empty dict when yaml module is not available.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config_file = temp_cwd / ".yamllint"
    config_file.write_text("rules:\n  line-length: 120\n")
    with patch("lintro.utils.native_parsers.yaml", None):
        result = _load_native_tool_config("yamllint")
        assert_that(result).is_empty()


def test_load_yamllint_config_no_config_file(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Return empty dict when no yamllint config file exists.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    result = _load_native_tool_config("yamllint")
    assert_that(result).is_empty()


def test_load_yamllint_config_invalid_yaml(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Return empty dict when yamllint config contains invalid YAML.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config_file = temp_cwd / ".yamllint"
    config_file.write_text("invalid: yaml: content: [")
    result = _load_native_tool_config("yamllint")
    assert_that(result).is_empty()


def test_load_yamllint_config_unicode_content(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load yamllint config with Unicode characters in values.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config_file = temp_cwd / ".yamllint"
    config_file.write_text("rules:\n  comments: 日本語\n")
    result = _load_native_tool_config("yamllint")
    assert_that(result["rules"]["comments"]).is_equal_to("日本語")
