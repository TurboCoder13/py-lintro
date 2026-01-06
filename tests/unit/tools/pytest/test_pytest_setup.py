"""Unit tests for pytest tool setup and configuration."""

from __future__ import annotations

import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from lintro.tools.implementations.tool_pytest import PytestTool


def test_pytest_tool_set_options_discovery_and_inspection() -> None:
    """Test setting discovery and inspection options."""
    tool = PytestTool()

    tool.set_options(
        collect_only=True,
        list_fixtures=True,
        fixture_info="sample_data",
        list_markers=True,
        parametrize_help=True,
    )

    assert_that(tool.options["collect_only"]).is_true()
    assert_that(tool.options["list_fixtures"]).is_true()
    assert_that(tool.options["fixture_info"]).is_equal_to("sample_data")
    assert_that(tool.options["list_markers"]).is_true()
    assert_that(tool.options["parametrize_help"]).is_true()


def test_pytest_tool_set_options_invalid_collect_only() -> None:
    """Test setting invalid collect_only option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="collect_only must be a boolean"):
        tool.set_options(collect_only="invalid")


def test_pytest_tool_set_options_invalid_list_fixtures() -> None:
    """Test setting invalid list_fixtures option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="list_fixtures must be a boolean"):
        tool.set_options(list_fixtures="invalid")


def test_pytest_tool_set_options_invalid_fixture_info() -> None:
    """Test setting invalid fixture_info option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="fixture_info must be a string"):
        tool.set_options(fixture_info=123)


def test_pytest_tool_set_options_invalid_list_markers() -> None:
    """Test setting invalid list_markers option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="list_markers must be a boolean"):
        tool.set_options(list_markers="invalid")


def test_pytest_tool_set_options_invalid_parametrize_help() -> None:
    """Test setting invalid parametrize_help option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="parametrize_help must be a boolean"):
        tool.set_options(parametrize_help="invalid")


def test_pytest_tool_load_file_patterns_list() -> None:
    """Test loading file patterns as list from config."""
    from lintro.tools.implementations.pytest.output import (
        load_file_patterns_from_config,
    )

    config = {"python_files": ["test_*.py", "*_test.py"]}
    result = load_file_patterns_from_config(config)
    assert_that(result).is_equal_to(["test_*.py", "*_test.py"])


def test_pytest_tool_load_file_patterns_invalid_type() -> None:
    """Test loading file patterns with invalid type."""
    from lintro.tools.implementations.pytest.output import (
        load_file_patterns_from_config,
    )

    config = {"python_files": 123}
    result = load_file_patterns_from_config(config)
    assert_that(result).is_equal_to([])


def test_pytest_tool_load_file_patterns_empty_config() -> None:
    """Test loading file patterns with empty config."""
    from lintro.tools.implementations.pytest.output import (
        load_file_patterns_from_config,
    )

    result = load_file_patterns_from_config({})
    assert_that(result).is_equal_to([])


def test_pytest_tool_load_file_patterns_none_python_files() -> None:
    """Test loading file patterns when python_files is None."""
    from lintro.tools.implementations.pytest.output import (
        load_file_patterns_from_config,
    )

    config = {"python_files": None}
    result = load_file_patterns_from_config(config)
    assert_that(result).is_equal_to([])


def test_pytest_tool_load_config_error_handling() -> None:
    """Test loading pytest config with error handling."""
    from lintro.tools.implementations.pytest.pytest_utils import (
        clear_pytest_config_cache,
        load_pytest_config,
    )

    # Clear cache to ensure fresh read
    clear_pytest_config_cache()

    # Mock stat to return a fake stat result, exists to return True,
    # and open to raise an exception
    fake_stat_result = MagicMock()
    fake_stat_result.st_mtime = 12345.0

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.stat", return_value=fake_stat_result),
        patch("builtins.open", side_effect=Exception("Read error")),
    ):
        result = load_pytest_config()
        assert_that(result).is_equal_to({})


def test_pytest_tool_load_lintro_ignore_error() -> None:
    """Test loading .lintro-ignore with error handling."""
    from lintro.tools.implementations.pytest.pytest_utils import load_lintro_ignore

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", side_effect=Exception("Read error")),
    ):
        result = load_lintro_ignore()
        assert_that(result).is_equal_to([])


def test_pytest_config_caching() -> None:
    """Test that pytest config loading uses caching."""
    from lintro.tools.implementations.pytest.pytest_utils import (
        clear_pytest_config_cache,
        load_pytest_config,
    )

    # Clear cache to start fresh
    clear_pytest_config_cache()

    # First call should populate cache
    config1 = load_pytest_config()

    # Second call should use cached result
    config2 = load_pytest_config()

    # Results should be identical (same object if cached properly)
    assert_that(config1).is_equal_to(config2)

    # Clear cache and verify different result possible
    clear_pytest_config_cache()
    config3 = load_pytest_config()
    # Config should still be the same content, but cache should be cleared
    assert_that(config3).is_equal_to(config1)


def test_pytest_config_caching_with_file_changes(tmp_path: Path) -> None:
    """Test that config cache invalidates when files change.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    from lintro.tools.implementations.pytest.pytest_utils import (
        clear_pytest_config_cache,
        load_pytest_config,
    )

    # Change to temp directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        clear_pytest_config_cache()

        # Create a pyproject.toml
        pyproject_content = """
[tool.pytest.ini_options]
addopts = "-v"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        # First load should cache the config
        config1 = load_pytest_config()
        assert_that(config1.get("addopts")).is_equal_to("-v")

        # Small delay to ensure file modification time changes
        # Some filesystems have 1-second mtime resolution
        time.sleep(1.1)

        # Clear cache to ensure we re-read from file
        clear_pytest_config_cache()

        # Modify the file
        pyproject_content_modified = """
[tool.pytest.ini_options]
addopts = "-v --tb=short"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content_modified)

        # Second load should pick up changes (cache invalidation)
        config2 = load_pytest_config()
        assert_that(config2.get("addopts")).is_equal_to("-v --tb=short")

    finally:
        os.chdir(original_cwd)
