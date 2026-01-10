"""Tests for BlackPlugin._build_common_args method."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.black import BlackPlugin


def test_build_common_args_empty_by_default(black_plugin: BlackPlugin) -> None:
    """Build common args returns empty list by default.

    Args:
        black_plugin: The BlackPlugin instance to test.
    """
    with patch.object(black_plugin, "_build_config_args", return_value=[]):
        args = black_plugin._build_common_args()
        assert_that(args).is_empty()


def test_build_common_args_with_line_length(black_plugin: BlackPlugin) -> None:
    """Build common args includes line length.

    Args:
        black_plugin: The BlackPlugin instance to test.
    """
    black_plugin.set_options(line_length=100)
    with patch.object(black_plugin, "_build_config_args", return_value=[]):
        args = black_plugin._build_common_args()
        assert_that(args).contains("--line-length")
        assert_that(args).contains("100")


def test_build_common_args_with_target_version(black_plugin: BlackPlugin) -> None:
    """Build common args includes target version.

    Args:
        black_plugin: The BlackPlugin instance to test.
    """
    black_plugin.set_options(target_version="py310")
    with patch.object(black_plugin, "_build_config_args", return_value=[]):
        args = black_plugin._build_common_args()
        assert_that(args).contains("--target-version")
        assert_that(args).contains("py310")


def test_build_common_args_with_fast(black_plugin: BlackPlugin) -> None:
    """Build common args includes fast flag.

    Args:
        black_plugin: The BlackPlugin instance to test.
    """
    black_plugin.set_options(fast=True)
    with patch.object(black_plugin, "_build_config_args", return_value=[]):
        args = black_plugin._build_common_args()
        assert_that(args).contains("--fast")


def test_build_common_args_with_preview(black_plugin: BlackPlugin) -> None:
    """Build common args includes preview flag.

    Args:
        black_plugin: The BlackPlugin instance to test.
    """
    black_plugin.set_options(preview=True)
    with patch.object(black_plugin, "_build_config_args", return_value=[]):
        args = black_plugin._build_common_args()
        assert_that(args).contains("--preview")


def test_build_common_args_with_config_injection(black_plugin: BlackPlugin) -> None:
    """Build common args uses config injection when available.

    Args:
        black_plugin: The BlackPlugin instance to test.
    """
    with patch.object(
        black_plugin,
        "_build_config_args",
        return_value=["--config", "/path/to/config"],
    ):
        args = black_plugin._build_common_args()
        assert_that(args).contains("--config")
        assert_that(args).contains("/path/to/config")
