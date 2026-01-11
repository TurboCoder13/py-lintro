"""Tests for BiomePlugin.set_options method."""

from __future__ import annotations

from typing import TYPE_CHECKING

from assertpy import assert_that

if TYPE_CHECKING:
    from lintro.tools.definitions.biome import BiomePlugin


def test_set_options_timeout(biome_plugin: BiomePlugin) -> None:
    """Set timeout option.

    Args:
        biome_plugin: The BiomePlugin instance to test.
    """
    biome_plugin.set_options(timeout=60)
    assert_that(biome_plugin.options.get("timeout")).is_equal_to(60)


def test_set_options_use_vcs_ignore(biome_plugin: BiomePlugin) -> None:
    """Set use_vcs_ignore option.

    Args:
        biome_plugin: The biome plugin instance to test.
    """
    biome_plugin.set_options(use_vcs_ignore=False)
    assert_that(biome_plugin.options.get("use_vcs_ignore")).is_false()


def test_set_options_verbose_fix_output(biome_plugin: BiomePlugin) -> None:
    """Set verbose_fix_output option.

    Args:
        biome_plugin: The biome plugin instance to test.
    """
    biome_plugin.set_options(verbose_fix_output=True)
    assert_that(biome_plugin.options.get("verbose_fix_output")).is_true()


def test_set_options_exclude_patterns(biome_plugin: BiomePlugin) -> None:
    """Set exclude_patterns option.

    Args:
        biome_plugin: The biome plugin instance to test.
    """
    patterns = ["node_modules", "dist"]
    biome_plugin.set_options(exclude_patterns=patterns)
    assert_that(biome_plugin.exclude_patterns).is_equal_to(patterns)


def test_set_options_include_venv(biome_plugin: BiomePlugin) -> None:
    """Set include_venv option.

    Args:
        biome_plugin: The biome plugin instance to test.
    """
    biome_plugin.set_options(include_venv=True)
    assert_that(biome_plugin.include_venv).is_true()


def test_set_options_no_options(biome_plugin: BiomePlugin) -> None:
    """Handle no options set - options should remain unchanged.

    Args:
        biome_plugin: The biome plugin instance to test.
    """
    initial_options = dict(biome_plugin.options)
    biome_plugin.set_options()
    assert_that(biome_plugin.options).is_equal_to(initial_options)
