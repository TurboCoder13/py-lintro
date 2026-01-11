"""Tests for _load_native_tool_config with prettier."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from assertpy import assert_that

from lintro.utils.native_parsers import _load_native_tool_config


def test_load_prettier_config_from_prettierrc(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load prettier config from .prettierrc file.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config_file = temp_cwd / ".prettierrc"
    config_file.write_text('{"tabWidth": 4, "semi": false}')
    result = _load_native_tool_config("prettier")
    assert_that(result).is_equal_to({"tabWidth": 4, "semi": False})


def test_load_prettier_config_from_prettierrc_json(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load prettier config from .prettierrc.json file.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    config_file = temp_cwd / ".prettierrc.json"
    config_file.write_text('{"printWidth": 100}')
    result = _load_native_tool_config("prettier")
    assert_that(result).is_equal_to({"printWidth": 100})


def test_load_prettier_config_from_package_json(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
) -> None:
    """Load prettier config from package.json prettier field.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
    """
    pkg_file = temp_cwd / "package.json"
    pkg_file.write_text('{"name": "test", "prettier": {"tabWidth": 2}}')
    result = _load_native_tool_config("prettier")
    assert_that(result).is_equal_to({"tabWidth": 2})


@pytest.mark.parametrize(
    ("package_content", "description"),
    [
        ('{"name": "test"}', "no_prettier_field"),
        ("not valid json", "invalid_json"),
        ('["invalid"]', "not_a_dict"),
        ('{"name": "test", "prettier": "invalid"}', "prettier_field_not_dict"),
    ],
    ids=[
        "package_json_no_prettier_field",
        "package_json_invalid_json",
        "package_json_not_dict",
        "prettier_field_not_dict",
    ],
)
def test_load_prettier_config_package_json_edge_cases(
    mock_empty_pyproject: MagicMock,
    temp_cwd: Path,
    package_content: str,
    description: str,
) -> None:
    """Return empty dict for various package.json edge cases.

    Args:
        mock_empty_pyproject: Mock for empty pyproject.toml.
        temp_cwd: Temporary current working directory.
        package_content: Content to write to package.json.
        description: Description of the test case.
    """
    pkg_file = temp_cwd / "package.json"
    pkg_file.write_text(package_content)
    result = _load_native_tool_config("prettier")
    assert_that(result).is_empty()
