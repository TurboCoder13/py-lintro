"""Tests for _load_json_config function."""

from __future__ import annotations

from pathlib import Path

import pytest
from assertpy import assert_that

from lintro.utils.native_parsers import _load_json_config


def test_load_json_config_valid_json_file(tmp_path: Path) -> None:
    """Load valid JSON configuration file and return its contents.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    config_file = tmp_path / "config.json"
    config_file.write_text('{"key": "value", "number": 42}')
    result = _load_json_config(config_file)
    assert_that(result).is_equal_to({"key": "value", "number": 42})


@pytest.mark.parametrize(
    ("content", "description"),
    [
        ("not valid json {", "invalid_json"),
        ('["item1", "item2"]', "non_dict_array"),
    ],
    ids=["invalid_json_syntax", "json_array_not_dict"],
)
def test_load_json_config_returns_empty_dict(
    tmp_path: Path,
    content: str,
    description: str,
) -> None:
    """Return empty dict for invalid JSON or non-dict JSON content.

    Args:
        tmp_path: Temporary directory path for test files.
        content: Invalid JSON content to write to file.
        description: Description of the test case.
    """
    config_file = tmp_path / "config.json"
    config_file.write_text(content)
    result = _load_json_config(config_file)
    assert_that(result).is_empty()


def test_load_json_config_non_existent_file(tmp_path: Path) -> None:
    """Return empty dict when the config file does not exist.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    config_file = tmp_path / "nonexistent.json"
    result = _load_json_config(config_file)
    assert_that(result).is_empty()


def test_load_json_config_unicode_file_path(tmp_path: Path) -> None:
    """Load JSON config from path with Unicode characters.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    config_dir = tmp_path / "配置"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    config_file.write_text('{"key": "value"}')
    result = _load_json_config(config_file)
    assert_that(result).is_equal_to({"key": "value"})


def test_load_json_config_empty_file(tmp_path: Path) -> None:
    """Return empty dict for empty JSON file.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    config_file = tmp_path / "empty.json"
    config_file.write_text("")
    result = _load_json_config(config_file)
    assert_that(result).is_empty()


def test_load_json_config_null_json(tmp_path: Path) -> None:
    """Return empty dict when JSON content is null.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    config_file = tmp_path / "null.json"
    config_file.write_text("null")
    result = _load_json_config(config_file)
    assert_that(result).is_empty()


def test_load_json_config_nested_empty_object(tmp_path: Path) -> None:
    """Load JSON with nested empty objects.

    Args:
        tmp_path: Temporary directory path for test files.
    """
    config_file = tmp_path / "config.json"
    config_file.write_text('{"outer": {"inner": {}}}')
    result = _load_json_config(config_file)
    assert_that(result["outer"]["inner"]).is_empty()
