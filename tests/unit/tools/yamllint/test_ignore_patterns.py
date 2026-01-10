"""Tests for YamllintPlugin ignore pattern handling."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import mock_open, patch

from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.yamllint import YamllintPlugin


# Tests for _load_yamllint_ignore_patterns method


def test_load_yamllint_ignore_patterns_no_config(
    yamllint_plugin: YamllintPlugin,
) -> None:
    """Returns empty list when no config file.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    result = yamllint_plugin._load_yamllint_ignore_patterns(config_file=None)
    assert_that(result).is_empty()


def test_load_yamllint_ignore_patterns_file_not_exists(
    yamllint_plugin: YamllintPlugin,
) -> None:
    """Returns empty list when config file does not exist.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    with patch("os.path.exists", return_value=False):
        result = yamllint_plugin._load_yamllint_ignore_patterns(
            config_file="/nonexistent.yml",
        )
        assert_that(result).is_empty()


def test_load_yamllint_ignore_patterns_with_patterns(
    yamllint_plugin: YamllintPlugin,
) -> None:
    """Returns ignore patterns from config file.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    yaml_content = """
rules:
  line-length:
    ignore:
      - test_samples/
      - fixtures/
"""
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = yamllint_plugin._load_yamllint_ignore_patterns(
                config_file="/project/.yamllint",
            )
            assert_that(result).contains("test_samples/")
            assert_that(result).contains("fixtures/")


def test_load_yamllint_ignore_patterns_with_string_pattern(
    yamllint_plugin: YamllintPlugin,
) -> None:
    """Returns ignore patterns when specified as string.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    yaml_content = """
rules:
  line-length:
    ignore: |
      test_samples/
      fixtures/
"""
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = yamllint_plugin._load_yamllint_ignore_patterns(
                config_file="/project/.yamllint",
            )
            assert_that(result).contains("test_samples/")
            assert_that(result).contains("fixtures/")


# Tests for _should_ignore_file method


def test_should_ignore_file_no_patterns(yamllint_plugin: YamllintPlugin) -> None:
    """Returns False when no ignore patterns.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    result = yamllint_plugin._should_ignore_file(
        file_path="test.yml",
        ignore_patterns=[],
    )
    assert_that(result).is_false()


def test_should_ignore_file_matches_prefix(yamllint_plugin: YamllintPlugin) -> None:
    """Returns True when file path starts with pattern.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    result = yamllint_plugin._should_ignore_file(
        file_path="test_samples/config.yml",
        ignore_patterns=["test_samples/"],
    )
    assert_that(result).is_true()


def test_should_ignore_file_matches_contains(yamllint_plugin: YamllintPlugin) -> None:
    """Returns True when pattern is contained in path.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    result = yamllint_plugin._should_ignore_file(
        file_path="/project/test_samples/config.yml",
        ignore_patterns=["test_samples/"],
    )
    assert_that(result).is_true()


def test_should_ignore_file_matches_glob(yamllint_plugin: YamllintPlugin) -> None:
    """Returns True when file matches glob pattern.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    result = yamllint_plugin._should_ignore_file(
        file_path="test.generated.yml",
        ignore_patterns=["*.generated.yml"],
    )
    assert_that(result).is_true()


def test_should_ignore_file_no_match(yamllint_plugin: YamllintPlugin) -> None:
    """Returns False when file does not match any pattern.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    result = yamllint_plugin._should_ignore_file(
        file_path="config.yml",
        ignore_patterns=["test_samples/", "fixtures/"],
    )
    assert_that(result).is_false()
