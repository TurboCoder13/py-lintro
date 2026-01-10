"""Tests for YamllintPlugin._find_yamllint_config method."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.yamllint import YamllintPlugin


def test_find_yamllint_config_not_found(yamllint_plugin: YamllintPlugin) -> None:
    """Returns None when no config file exists.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    with patch("os.path.exists", return_value=False):
        result = yamllint_plugin._find_yamllint_config(search_dir="/nonexistent")
        assert_that(result).is_none()


def test_find_yamllint_config_found(yamllint_plugin: YamllintPlugin) -> None:
    """Returns path when config exists.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """

    def mock_exists(path: str) -> bool:
        return path.endswith(".yamllint")

    with patch("os.path.exists", side_effect=mock_exists):
        with patch("os.getcwd", return_value="/project"):
            with patch(
                "os.path.abspath",
                side_effect=lambda p: p if p.startswith("/") else f"/project/{p}",
            ):
                result = yamllint_plugin._find_yamllint_config(search_dir="/project")
                assert_that(result).is_not_none()
                assert_that(result).contains(".yamllint")


def test_find_yamllint_config_uses_explicit_config_file(
    yamllint_plugin: YamllintPlugin,
) -> None:
    """Returns explicitly set config_file option.

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    yamllint_plugin.set_options(config_file="/custom/config.yml")
    result = yamllint_plugin._find_yamllint_config()
    assert_that(result).is_equal_to("/custom/config.yml")


def test_find_yamllint_config_returns_none_when_config_data_set(
    yamllint_plugin: YamllintPlugin,
) -> None:
    """Returns None when config_data is set (inline config).

    Args:
        yamllint_plugin: The YamllintPlugin instance to test.
    """
    yamllint_plugin.set_options(config_data="extends: default")
    result = yamllint_plugin._find_yamllint_config()
    assert_that(result).is_none()
