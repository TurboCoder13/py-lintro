"""Tests for pydoclint plugin configuration initialization."""

from __future__ import annotations

from unittest.mock import patch

from assertpy import assert_that

from lintro.tools.definitions.pydoclint import PydoclintPlugin


def test_plugin_init_with_timeout_config() -> None:
    """Plugin initialization applies timeout from config."""
    config = {"timeout": 60}
    with patch(
        "lintro.tools.definitions.pydoclint.load_pydoclint_config",
        return_value=config,
    ):
        plugin = PydoclintPlugin()

    assert_that(plugin.options.get("timeout")).is_equal_to(60)


def test_plugin_init_with_style_config() -> None:
    """Plugin initialization applies style from config."""
    config = {"style": "numpy"}
    with patch(
        "lintro.tools.definitions.pydoclint.load_pydoclint_config",
        return_value=config,
    ):
        plugin = PydoclintPlugin()

    assert_that(plugin.options.get("style")).is_equal_to("numpy")


def test_plugin_definition_has_empty_conflicts_with() -> None:
    """Plugin definition has empty conflicts_with list."""
    with patch(
        "lintro.tools.definitions.pydoclint.load_pydoclint_config",
        return_value={},
    ):
        plugin = PydoclintPlugin()

    assert_that(plugin.definition.conflicts_with).is_empty()
